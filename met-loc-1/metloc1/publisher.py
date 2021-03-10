import base64
import json
import logging
import random
import time
from datetime import datetime, timezone
from uuid import uuid4

from iotic.web.rest.client.qapi import LangLiteral, Value, GeoLocationUpdate, GeoLocation
from iotics.host.api.data_types import BasicDataTypes

from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder, AgentAuth
from iotics.host.exceptions import DataSourcesConfigurationError, DataSourcesError, DataSourcesQApiError
from metloc1.exceptions import MetofficeLocationOneBaseException
from metloc1.conf import MetofficeLocationOneConf

logger = logging.getLogger(__name__)

TWIN_NAME = 'MetofficeLocation1'


def is_enabled_for_debug():
    return logger.isEnabledFor(logging.DEBUG)


class MetofficeLocationOne:  # MetofficeLocationHandler

    def __init__(self, agent_auth: AgentAuth, qapi_factory: QApiFactory, update_frequency_seconds: float):
        self.update_frequency_seconds = update_frequency_seconds
        self.qapi_factory = qapi_factory
        self.agent_auth = agent_auth

    def _create_twin(self) -> str:
        # Create an twin id in the registerer
        twin_id, _, _ = self.agent_auth.make_twin_id(TWIN_NAME)

        # Create the twin
        api = self.qapi_factory.get_twin_api()
        api.create_twin(twin_id)
        return twin_id

    def _set_twin_meta(self, twin_id: str):
        label = 'Metoffice Location One'
        description = 'Twin of the Metoffice Location 1'
        api = self.qapi_factory.get_twin_api()

        # Set twin location to London
        # This will make the twin visible in Iotics Cloud and it will enable the search by location.
        london_location = GeoLocationUpdate(location=GeoLocation(lat=51.507359, lon=-0.136439))

        api.update_twin(
            twin_id,
            add_tags=['metoffice', 'connector_handler'],
            add_labels=[LangLiteral(value=label, lang='en')],
            add_comments=[LangLiteral(value=description, lang='en')],
            location=london_location,
        )
        logging.debug('Created Twin %s', api.describe_twin(twin_id=twin_id))

    def _create_feed(self, twin_id: str) -> str:
        api = self.qapi_factory.get_feed_api()
        feed_name = 'call_api'
        api.create_feed(twin_id, feed_name)
        return feed_name

    def _set_feed_meta(self, twin_id: str, feed_name: str):
        label = 'Api detail'
        description = f'Awesome feed generating a temperature in Celsius each {self.update_frequency_seconds} seconds'
        api = self.qapi_factory.get_feed_api()

        api.update_feed(
            twin_id, feed_name,
            add_labels=[LangLiteral(value=label, lang='en')],
            add_comments=[LangLiteral(value=description, lang='en')],
            # Whether this feed's most recent data can be retrieved via the InterestApi
            store_last=True,
            add_values=[
                Value(
                    label='url',
                    data_type=BasicDataTypes.STRING.value,
                    comment='a random temperature in Celsius',
                    unit='http://purl.obolibrary.org/obo/UO_0000027'
                ),
                Value(
                    label='api_key',
                    data_type=BasicDataTypes.STRING.value,
                    comment='a random temperature in Celsius',
                    unit='http://purl.obolibrary.org/obo/UO_0000027'
                ),
                Value(
                    label='template_id',
                    data_type=BasicDataTypes.STRING.value,
                    comment='a random temperature in Celsius',
                    unit='http://purl.obolibrary.org/obo/UO_0000027'
                )
            ]
        )
        logging.debug('Created Feed %s', api.describe_feed(twin_id=twin_id, feed_id=feed_name))

    def _share_feed_data(self, twin_id: str, feed_name: str):
        non_encoded_data = {
            'url': 'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/99139?res=3hourly&key=3ba739f5-b717-4c31-8d70-b841da7d2863',
            'api_key': '3ba739f5-b717-4c31-8d70-b841da7d2863',
            'template_id': 'weather_forecast'
        }
        json_data = json.dumps(non_encoded_data)
        try:
            base64_encoded_data = base64.b64encode(json_data.encode()).decode()
        except TypeError as err:
            raise MetofficeLocationOneBaseException(
                f'Can not encode data to share from {twin_id}/{feed_name}: {err}, {json_data}'
            ) from err

        api = self.qapi_factory.get_feed_api()
        api.share_feed_data(
            twin_id, feed_name,
            data=base64_encoded_data, mime='application/json',
            occurred_at=datetime.now(tz=timezone.utc).isoformat()
        )

        return non_encoded_data

    def setup(self):
        """Create an twin and set its meta data. Create a feed an set its meta data."""

        logger.debug('Publisher setup')
        twin_id = self._create_twin()
        self._set_twin_meta(twin_id)

        feed_name = self._create_feed(twin_id)
        self._set_feed_meta(twin_id, feed_name)

        return twin_id, feed_name

    def publish(self, twin_id: str, feed_name: str):
        """Publish a new random temperature in Celsius."""

        try:
            non_encoded_data = self._share_feed_data(twin_id, feed_name)
        except DataSourcesQApiError as err:
            logger.error('Publishing QAPI error: %s', err, exc_info=is_enabled_for_debug())
        else:
            logger.info('Published %s', non_encoded_data)

    def run(self):
        logger.info('Publisher started')
        twin_id, feed_name = self.setup()
        while True:
            self.publish(twin_id, feed_name)
            logger.info('End of loop, will sleep for %s seconds', self.update_frequency_seconds)
            time.sleep(60)


def run_publisher():
    """Publisher entry point called by the console script declared in the setup.cfg."""

    try:
        conf = MetofficeLocationOneConf.get_conf()
        logging.basicConfig(
            format='%(asctime)s %(levelname)s [%(name)s] {%(threadName)s} %(message)s', level=conf.root_log_level
        )
        agent_auth = AgentAuthBuilder.build_agent_auth(conf.auth.resolver_host, conf.auth.seed, conf.auth.user)
        qapi_factory = QApiFactory(conf, agent_auth, client_app_id=f'metloc1_{uuid4()}')

        publisher = MetofficeLocationOne(agent_auth, qapi_factory, conf.update_frequency_seconds)
        publisher.run()
    except MetofficeLocationOneBaseException as err:
        logger.error('Publisher error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesConfigurationError as err:
        logger.error('Configuration error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesError as err:
        logger.error('MetofficeLocationOne} error: %s', err, exc_info=is_enabled_for_debug())
    except Exception as err:  # pylint: disable=W0703
        logger.error('Unexpected error: %s', err, exc_info=is_enabled_for_debug())


if __name__ == '__main__':
    run_publisher()
