import base64
import json
import logging
from time import sleep
from uuid import uuid4

from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuth, AgentAuthBuilder
from iotics.host.exceptions import (
    DataSourcesConfigurationError,
    DataSourcesError,
    DataSourcesSearchTimeout,
    DataSourcesStompError,
    DataSourcesStompNotConnected,
)

from randfol.conf import RandomTempFollowerConf
from randfol.exceptions import RandomTempFollowerBaseException

from .dbengine.sqlite import SensorReading, SQLite

logger = logging.getLogger(__name__)
# turn down stomp logging
logging.getLogger("stomp.py").setLevel(level=logging.ERROR)


def is_enabled_for_debug():
    return logger.isEnabledFor(logging.DEBUG)


class RandomTempFollower:
    def __init__(
        self,
        agent_auth: AgentAuth,
        qapi_factory: QApiFactory,
        update_frequency_seconds: float,
    ):
        self.twin_api = qapi_factory.get_twin_api()
        self.search_api = qapi_factory.get_search_api()
        self.follow_api = qapi_factory.get_follow_api()
        self.interest_api = qapi_factory.get_interest_api()
        self.agent_auth = agent_auth
        self.loop_time = update_frequency_seconds
        self.follower_twin_id = None
        self.db_handler = SQLite()

    def create_follower_twin(self):
        twin_id = self.agent_auth.make_twin_id("RandomTempFollower")
        self.twin_api.create_twin(twin_id)
        self.follower_twin_id = twin_id

    def follow_callback(self, header, body):  # pylint: disable=W0613
        decoded_data = base64.b64decode(body.payload.feed_data.data).decode("ascii")
        reading = json.loads(decoded_data)
        timestamp = body.payload.feed_data.occurred_at.isoformat()
        temperature = reading["temp"]
        sensor_id = reading["sens_id"]

        logger.info("Received temperature data %s at time %s", reading, timestamp)

        sensor_reading = SensorReading(
            timestamp=timestamp, sensor_id=sensor_id, reading_value=temperature
        )

        self.db_handler.store(sensor_reading)

    def get_most_recent_data(self, followed_twin_id: str, feed_id: str):
        """Get feed's most recent data via the InterestApi
        Note: the feed metadata must include store_last=True
        """
        logger.info("Get most recent data via InterestApi")
        most_recent_data = self.interest_api.get_feed_last_stored_local(
            follower_twin_id=self.follower_twin_id,
            followed_twin_id=followed_twin_id,
            feed_id=feed_id,
        )
        if not most_recent_data.feed_data:
            logger.info("No most recent data found.")
            return

        decoded_data = base64.b64decode(most_recent_data.feed_data.data).decode()
        temperature = json.loads(decoded_data)
        logger.info("Most recent data %s", temperature)

    def follow_twins(self):
        """Find and follow twins"""
        search_resp_gen = None
        logger.info("Searching for twins.")
        try:
            # search for twins
            # note: a generator is returned because responses are yielded
            # as they come in asynchronously from the network of hosts
            search_resp_gen = self.search_api.search_twins(text="Random")
        except DataSourcesSearchTimeout as timeout_ex:
            logger.warning("Timed out searching for twins: %s", timeout_ex)
        except DataSourcesStompError as ex:
            logger.error("Error searching for twins: %s", ex)
        except DataSourcesStompNotConnected:
            logger.warning("Cant search for twins, stomp not currently connected")

        if not search_resp_gen:
            logger.info("No twins found")
            return

        found_twins = 0
        subscription_count = 0
        for search_resp in search_resp_gen:
            for twin in search_resp.twins:
                found_twins += 1
                try:
                    # follow twin's feed
                    subscription_id = self.follow_api.subscribe_to_feed(
                        self.follower_twin_id,
                        twin.id.value,
                        "random_temperature_feed",
                        self.follow_callback,
                    )
                except DataSourcesStompNotConnected:
                    logger.warning("Cant follow twin, stomp not currently connected")
                    break

                if subscription_id:
                    subscription_count += 1
                    logger.info("Subscribed to feed on twin %s", twin.id.value)
                    # Optional call to get the feed's most recent data via the InterestApi
                    # This call is not needed to perform a follow
                    self.get_most_recent_data(twin.id.value, "random_temperature_feed")

        logger.info(
            "Found %s twins; subscribed to %s new feeds.",
            found_twins,
            subscription_count,
        )

    def run(self):
        logger.info("Follower started")
        self.create_follower_twin()

        while True:
            self.follow_twins()
            logger.info("Sleeping for %s seconds", self.loop_time)
            sleep(self.loop_time)


def run_follower():
    """Follower entry point called by the console script declared in the setup.cfg"""

    try:
        conf = RandomTempFollowerConf.get_conf()
        logging.basicConfig(
            format="%(asctime)s %(levelname)s [%(name)s] {%(threadName)s} %(message)s",
            level=conf.root_log_level,
        )
        agent_auth = AgentAuthBuilder.build_agent_auth(
            resolver_url=conf.auth.resolver_host,
            user_seed=conf.auth.user_seed,
            user_key_name=conf.auth.user_key_name,
            agent_seed=conf.auth.agent_seed,
            agent_key_name=conf.auth.agent_key_name,
            user_name=conf.auth.user_name,
            agent_name=conf.auth.agent_name,
        )
        qapi_factory = QApiFactory(conf, agent_auth, client_app_id=f"randfol_{uuid4()}")

        follower = RandomTempFollower(
            agent_auth, qapi_factory, conf.update_frequency_seconds
        )
        follower.run()
    except RandomTempFollowerBaseException as err:
        logger.error("Follower error: %s", err, exc_info=is_enabled_for_debug())
    except DataSourcesConfigurationError as err:
        logger.error("Configuration error: %s", err, exc_info=is_enabled_for_debug())
    except DataSourcesError as err:
        logger.error(
            "RandomTempFollower} error: %s", err, exc_info=is_enabled_for_debug()
        )
    except Exception as err:  # pylint: disable=W0703
        logger.error("Unexpected error: %s", err, exc_info=is_enabled_for_debug())


if __name__ == "__main__":
    run_follower()
