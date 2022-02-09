import base64
import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Tuple
from uuid import uuid4

from iotic.web.rest.client.qapi import (
    LangLiteral,
    Value,
    GeoLocation,
    ModelProperty,
    Visibility,
    Uri,
    UpsertFeedWithMeta,
)
from iotics.host.api.data_types import BasicDataTypes

from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder, AgentAuth
from iotics.host.exceptions import (
    DataSourcesConfigurationError,
    DataSourcesError,
    DataSourcesQApiError,
)
from randpub.exceptions import RandomTempPublisherBaseException
from randpub.conf import RandomTempPublisherConf

logger = logging.getLogger(__name__)

TWIN_NAME = "Random temperature twin"


def is_enabled_for_debug():
    return logger.isEnabledFor(logging.DEBUG)


class RandomTempPublisher:
    def __init__(
        self,
        agent_auth: AgentAuth,
        qapi_factory: QApiFactory,
        update_frequency_seconds: float,
    ):
        self.update_frequency_seconds = update_frequency_seconds
        self.twin_api = qapi_factory.get_twin_api()
        self.feed_api = qapi_factory.get_feed_api()
        self.agent_auth = agent_auth

    def _create_twin_and_feed(self) -> Tuple[str, str]:
        # Create a twin id in the resolver
        twin_id = self.agent_auth.make_twin_id(TWIN_NAME)

        # Create the twin with metadata and feed
        # Properties of type http://www.w3.org/2000/01/rdf-schema#label and #comments will be indexed to allow
        # retrieval of twin via search by text
        twin_label = ModelProperty(
            key="http://www.w3.org/2000/01/rdf-schema#label",
            lang_literal_value=LangLiteral(lang="en", value="Random awesome twin"),
        )
        twin_description = ModelProperty(
            key="http://www.w3.org/2000/01/rdf-schema#comment",
            lang_literal_value=LangLiteral(
                lang="en", value="The first twin we made in Iotics"
            ),
        )
        feed_label = ModelProperty(
            key="http://www.w3.org/2000/01/rdf-schema#label",
            lang_literal_value=LangLiteral(lang="en", value="Random temperature feed"),
        )
        feed_description = ModelProperty(
            key="http://www.w3.org/2000/01/rdf-schema#comment",
            lang_literal_value=LangLiteral(
                lang="en",
                value=f"Awesome feed generating a temperature in Celsius each {self.update_frequency_seconds} seconds",
            ),
        )
        # Allow any host from the network to interact with this twin
        allow_all_hosts = ModelProperty(
            key="http://data.iotics.com/public#hostAllowList",
            uri_value=Uri(value="http://data.iotics.com/public#allHosts"),
        )
        # Set twin location to London
        # This will make the twin visible in Iotics Cloud and it will enable the search by location.
        london_location = GeoLocation(lat=51.507359, lon=-0.136439)

        feed_name = "random_temperature_feed"
        self.twin_api.upsert_twin(
            twin_id,
            visibility=Visibility.PRIVATE,
            properties=[
                twin_label,
                twin_description,
                allow_all_hosts,
            ],
            location=london_location,
            feeds=[
                UpsertFeedWithMeta(
                    id=feed_name,
                    store_last=True,
                    properties=[feed_label, feed_description],
                    values=[
                        Value(
                            label="temp",
                            data_type=BasicDataTypes.DECIMAL.value,
                            comment="a random temperature in Celsius",
                            unit="http://purl.obolibrary.org/obo/UO_0000027",
                        ),
                        Value(
                            label="sens_id",
                            data_type=BasicDataTypes.INTEGER.value,
                            comment="a random sensor id",
                        ),
                    ],
                )
            ],
        )

        logging.info(
            "Created Feed and twin %s",
            self.feed_api.describe_feed(twin_id=twin_id, feed_id=feed_name),
        )
        return twin_id, feed_name

    def _share_feed_data(self, twin_id: str, feed_name: str):
        non_encoded_data = {
            "temp": round(random.uniform(-10.0, 45.0), 2),
            "sens_id": random.randint(1, 5),
        }
        json_data = json.dumps(non_encoded_data)
        try:
            base64_encoded_data = base64.b64encode(json_data.encode()).decode()
        except TypeError as err:
            raise RandomTempPublisherBaseException(
                f"Can not encode data to share from {twin_id}/{feed_name}: {err}, {json_data}"
            ) from err

        self.feed_api.share_feed_data(
            twin_id,
            feed_name,
            data=base64_encoded_data,
            mime="application/json",
            occurred_at=datetime.now(tz=timezone.utc).isoformat(),
        )

        return non_encoded_data

    def setup(self):
        """Create an twin and set its metadata. Create a feed an set its metadata."""

        logger.info("Publisher setup")
        twin_id, feed_name = self._create_twin_and_feed()
        return twin_id, feed_name

    def publish(self, twin_id: str, feed_name: str):
        """Publish a new random temperature in Celsius."""

        try:
            non_encoded_data = self._share_feed_data(twin_id, feed_name)
        except DataSourcesQApiError as err:
            logger.error(
                "Publishing QAPI error: %s", err, exc_info=is_enabled_for_debug()
            )
        else:
            logger.info("Published %s", non_encoded_data)

    def run(self):
        logger.info("Publisher started")
        twin_id, feed_name = self.setup()
        while True:
            self.publish(twin_id, feed_name)
            logger.info(
                "End of loop, will sleep for %s seconds", self.update_frequency_seconds
            )
            time.sleep(self.update_frequency_seconds)


def run_publisher():
    """Publisher entry point called by the console script declared in the setup.cfg."""

    try:
        conf = RandomTempPublisherConf.get_conf()
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
        qapi_factory = QApiFactory(conf, agent_auth, client_app_id=f"randpub_{uuid4()}")

        publisher = RandomTempPublisher(
            agent_auth, qapi_factory, conf.update_frequency_seconds
        )
        publisher.run()
    except RandomTempPublisherBaseException as err:
        logger.error("Publisher error: %s", err, exc_info=is_enabled_for_debug())
    except DataSourcesConfigurationError as err:
        logger.error("Configuration error: %s", err, exc_info=is_enabled_for_debug())
    except DataSourcesError as err:
        logger.error(
            "RandomTempPublisher} error: %s", err, exc_info=is_enabled_for_debug()
        )
    except Exception as err:  # pylint: disable=W0703
        logger.error("Unexpected error: %s", err, exc_info=is_enabled_for_debug())


if __name__ == "__main__":
    run_publisher()
