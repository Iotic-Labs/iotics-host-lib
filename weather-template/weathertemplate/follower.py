import base64
import json
import logging
from time import sleep
from uuid import uuid4
from queue import Queue

from iotic.web.rest.client.qapi import LangLiteral, Value, GeoLocationUpdate, GeoLocation
from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder, AgentAuth
from iotics.host.exceptions import (
    DataSourcesConfigurationError, DataSourcesError, DataSourcesSearchTimeout,
    DataSourcesStompError, DataSourcesStompNotConnected
)
from iotics.host.api.data_types import BasicDataTypes

from weathertemplate.exceptions import WeatherTemplateBaseException
from weathertemplate.conf import WeatherTemplateConf

logger = logging.getLogger(__name__)
# turn down stomp logging
logging.getLogger('stomp.py').setLevel(level=logging.ERROR)


def is_enabled_for_debug():
    return logger.isEnabledFor(logging.DEBUG)


class WeatherTemplate:

    def __init__(self, agent_auth: AgentAuth, qapi_factory: QApiFactory, update_frequency_seconds: float):
        self.twin_api = qapi_factory.get_twin_api()
        self.search_api = qapi_factory.get_search_api()
        self.follow_api = qapi_factory.get_follow_api()
        self.interest_api = qapi_factory.get_interest_api()
        self.feed_api = qapi_factory.get_feed_api()
        self.agent_auth = agent_auth
        self.loop_time = update_frequency_seconds
        self.follower_twin_id = None
        self._api_response_queue = Queue()

    def _create_twin(self) -> str:
        # Create an twin id in the registerer
        twin_id, _, _ = self.agent_auth.make_twin_id('weather_template')

        # Create the twin
        self.twin_api.create_twin(twin_id)
        self.follower_twin_id = twin_id

        return twin_id

    def _set_twin_meta(self, twin_id: str):
        label = 'Call Api'
        description = 'Twin of the call api'

        # Set twin location to London
        # This will make the twin visible in Iotics Cloud and it will enable the search by location.
        london_location = GeoLocationUpdate(location=GeoLocation(lat=51.507359, lon=-0.136439))

        self.twin_api.update_twin(
            twin_id,
            add_tags=['template_handler', 'function'],
            add_labels=[LangLiteral(value=label, lang='en')],
            add_comments=[LangLiteral(value=description, lang='en')],
            location=london_location,
        )
        logging.debug('Created Twin %s', self.twin_api.describe_twin(twin_id=twin_id))

    def _create_feed(self, twin_id: str) -> str:
        feed_name = 'template_filled_in'
        self.feed_api.create_feed(twin_id, feed_name)
        return feed_name

    def _set_feed_meta(self, twin_id: str, feed_name: str):
        label = 'template filled in'
        description = f'Awesome feed generating a temperature in Celsius each {self.loop_time} seconds'

        self.feed_api.update_feed(
            twin_id, feed_name,
            add_labels=[LangLiteral(value=label, lang='en')],
            add_comments=[LangLiteral(value=description, lang='en')],
            # Whether this feed's most recent data can be retrieved via the InterestApi
            store_last=True,
            add_values=[
                Value(
                    label='template_filled',
                    data_type=BasicDataTypes.STRING.value,
                    comment='a random temperature in Celsius',
                    unit='http://purl.obolibrary.org/obo/UO_0000027'
                )
            ]
        )
        logging.debug('Created Feed %s', self.feed_api.describe_feed(twin_id=twin_id, feed_id=feed_name))

    @staticmethod
    def follow_callback(header, body):  # pylint: disable=W0613
        decoded_data = base64.b64decode(body.payload.feed_data.data).decode('ascii')
        api_response = json.loads(decoded_data)
        timestamp = body.payload.feed_data.occurred_at.isoformat()

        logger.info('Received temperature data %s at time %s', temperature, timestamp)
        self._api_response_queue.put(api_response)


    def get_most_recent_data(self, followed_twin_id: str, feed_id: str):
        """ Get feed's most recent data via the InterestApi
            Note: the feed meta data must include store_last=True
        """
        logger.info('Get most recent data via InterestApi')
        most_recent_data = self.interest_api.get_feed_last_stored_local(
            follower_twin_id=self.follower_twin_id,
            followed_twin_id=followed_twin_id,
            feed_id=feed_id
        )
        decoded_data = base64.b64decode(most_recent_data.feed_data.data).decode()
        temperature = json.loads(decoded_data)
        logger.info('Most recent data %s', temperature)

    def follow_twins(self):
        """Find and follow twins"""
        search_resp_gen = None
        logger.info('Searching for twins.')
        try:
            # search for twins
            # note: a generator is returned because responses are yielded
            # as they come in asynchronously from the network of hosts
            search_resp_gen = self.search_api.search_twins(text='function')
        except DataSourcesSearchTimeout as timeout_ex:
            logger.warning('Timed out searching for twins: %s', timeout_ex)
        except DataSourcesStompError as ex:
            logger.error('Error searching for twins: %s', ex)
        except DataSourcesStompNotConnected:
            logger.warning('Cant search for twins, stomp not currently connected')

        if not search_resp_gen:
            logger.info('No twins found')
            return

        for search_resp in search_resp_gen:
            for twin in search_resp.twins:
                subscription_id = None

                try:
                    # follow twin's feed
                    subscription_id = self.follow_api.subscribe_to_feed(
                        self.follower_twin_id, twin.id.value, 'data_source_response', self.follow_callback
                    )
                except DataSourcesStompNotConnected:
                    logger.warning('Cant follow twin, stomp not currently connected')
                    break

                if subscription_id:
                    logger.info('Subscribed to feed on twin %s', twin.id.value)
                    # Optional call to get the feed's most recent data via the InterestApi
                    # This call is not needed to perform a follow
                    self.get_most_recent_data(twin.id.value, 'data_source_response')

    def _get_data_from_queue(self):
        api_response = self._api_response_queue.get()

        return api_response

    def _setup(self):
        """Create an twin and set its meta data. Create a feed an set its meta data."""

        logger.debug('Synthesiser setup')
        twin_id = self._create_twin()
        self._set_twin_meta(twin_id)

        feed_name = self._create_feed(twin_id)
        self._set_feed_meta(twin_id, feed_name)

        return twin_id, feed_name

    def run(self):
        logger.info('Synthesiser started')
        self._setup()

        while True:
            self.follow_twins()
            api_response = self._get_data_from_queue()
            if api_response:
                logger.info('api_response: %s', api_response)


def run_follower():
    """Follower entry point called by the console script declared in the setup.cfg"""

    try:
        conf = WeatherTemplateConf.get_conf()
        logging.basicConfig(
            format='%(asctime)s %(levelname)s [%(name)s] {%(threadName)s} %(message)s', level=conf.root_log_level
        )
        agent_auth = AgentAuthBuilder.build_agent_auth(conf.auth.resolver_host, conf.auth.seed, conf.auth.user)
        qapi_factory = QApiFactory(conf, agent_auth, client_app_id=f'weathertemplate_{uuid4()}')

        follower = WeatherTemplate(agent_auth, qapi_factory, conf.update_frequency_seconds)
        follower.run()
    except WeatherTemplateBaseException as err:
        logger.error('Follower error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesConfigurationError as err:
        logger.error('Configuration error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesError as err:
        logger.error('WeatherTemplate} error: %s', err, exc_info=is_enabled_for_debug())
    except Exception as err:  # pylint: disable=W0703
        logger.error('Unexpected error: %s', err, exc_info=is_enabled_for_debug())


if __name__ == '__main__':
    run_follower()
