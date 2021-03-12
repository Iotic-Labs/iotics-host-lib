import base64
import json
import logging
# from time import sleep
from uuid import uuid4
from queue import Queue
from collections import namedtuple
import requests
from datetime import datetime, timezone

from iotic.web.rest.client.qapi import LangLiteral, Value, GeoLocationUpdate, GeoLocation
from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder, AgentAuth
from iotics.host.exceptions import (
    DataSourcesConfigurationError, DataSourcesError, DataSourcesSearchTimeout,
    DataSourcesStompError, DataSourcesStompNotConnected, DataSourcesQApiError
)
from iotics.host.api.data_types import BasicDataTypes

from callapi.exceptions import CallApiBaseException
from callapi.conf import CallApiConf

logger = logging.getLogger(__name__)
# turn down stomp logging
logging.getLogger('stomp.py').setLevel(level=logging.ERROR)


def is_enabled_for_debug():
    return logger.isEnabledFor(logging.DEBUG)


DataToFetch = namedtuple('DataToFetch', 'url template_id api_key')


class CallApi:
    def __init__(self, agent_auth: AgentAuth, qapi_factory: QApiFactory, update_frequency_seconds: float):
        self.twin_api = qapi_factory.get_twin_api()
        self.search_api = qapi_factory.get_search_api()
        self.follow_api = qapi_factory.get_follow_api()
        self.interest_api = qapi_factory.get_interest_api()
        self.feed_api = qapi_factory.get_feed_api()
        self.agent_auth = agent_auth
        self.loop_time = update_frequency_seconds
        self.follower_twin_id = None
        self._data_to_fetch_queue = Queue()
        self._template_twin_dict = dict()

    def _create_twin(self) -> str:
        # Create an twin id in the registerer
        twin_id, _, _ = self.agent_auth.make_twin_id('CallApi')

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
            add_tags=['call_api'],
            add_labels=[LangLiteral(value=label, lang='en')],
            add_comments=[LangLiteral(value=description, lang='en')],
            location=london_location,
        )
        logging.debug('Created Twin %s', self.twin_api.describe_twin(twin_id=twin_id))

    def _create_feed(self, twin_id: str) -> str:
        feed_name = 'data_source_response'
        self.feed_api.create_feed(twin_id, feed_name)
        return feed_name

    def _set_feed_meta(self, twin_id: str, feed_name: str):
        label = 'data source response'
        description = f'Awesome feed generating a temperature in Celsius each {self.loop_time} seconds'

        self.feed_api.update_feed(
            twin_id, feed_name,
            add_labels=[LangLiteral(value=label, lang='en')],
            add_comments=[LangLiteral(value=description, lang='en')],
            # Whether this feed's most recent data can be retrieved via the InterestApi
            store_last=True,
            add_values=[
                Value(
                    label='data',
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
        logging.debug('Created Feed %s', self.feed_api.describe_feed(twin_id=twin_id, feed_id=feed_name))

    def follow_callback(self, header, body):  # pylint: disable=W0613
        decoded_data = base64.b64decode(body.payload.feed_data.data).decode('ascii')
        feed_data = json.loads(decoded_data)
        timestamp = body.payload.feed_data.occurred_at.isoformat()

        logger.info('header: %s', header)

        logger.info('Received api_call data %s at time %s', feed_data, timestamp)
        self._data_to_fetch_queue.put(
            DataToFetch(
                url=feed_data.get('url'),
                api_key=feed_data.get('api_key'),
                template_id=feed_data.get('template_id')
            )
        )

    @staticmethod
    def _call_api(api_to_call):
        api_data = None

        try:
            # headers = api_to_call.get(headers)
            # url = api_to_call.get(url)

            # if headers:
            #     req = requests.get(url=url, headers=headers)
            # else:
            #     req = requests.get(url=url)
            req = requests.get(url=api_to_call.url)
            req.raise_for_status()
        except Exception as ex:  # pylint: disable=broad-except
            raise CallApiBaseException(
                f'API call failure for stations list: {ex}'
            ) from ex
        else:
            try:
                if req.encoding is None:
                    req.encoding = 'utf-8'
                api_data = req.json()
            except ValueError as ex:
                raise CallApiBaseException(
                    f'Decoding JSON has failed: {ex}'
                ) from ex

        return api_data

    def follow_twins(self):
        """Find and follow twins"""
        search_resp_gen_connector_handler = None
        search_resp_gen_template_handler = None
        logger.debug('Searching for twins.')
        try:
            # search for twins
            # note: a generator is returned because responses are yielded
            # as they come in asynchronously from the network of hosts
            search_resp_gen_connector_handler = self.search_api.search_twins(text='connector_handler')
            search_resp_gen_template_handler = self.search_api.search_twins(text='template_handler')
        except DataSourcesSearchTimeout as timeout_ex:
            logger.warning('Timed out searching for twins: %s', timeout_ex)
        except DataSourcesStompError as ex:
            logger.error('Error searching for twins: %s', ex)
        except DataSourcesStompNotConnected:
            logger.warning('Cant search for twins, stomp not currently connected')

        if not search_resp_gen_connector_handler:
            logger.info('No twins found')
            return

        for search_resp in search_resp_gen_connector_handler:
            for twin in search_resp.twins:
                subscription_id = None

                try:
                    # follow twin's feed
                    subscription_id = self.follow_api.subscribe_to_feed(
                        self.follower_twin_id, twin.id.value, 'call_api', self.follow_callback
                    )
                except DataSourcesStompNotConnected:
                    logger.warning('Cant follow twin, stomp not currently connected')
                    break

                if subscription_id:
                    logger.info('Subscribed to feed on twin %s', twin.id.value)

        for search_resp in search_resp_gen_template_handler:
            for twin in search_resp.twins:
                subscription_id = None

                try:
                    # follow twin's feed
                    subscription_id = self.follow_api.subscribe_to_feed(
                        self.follower_twin_id, twin.id.value, 'template_filled_in', self.follow_callback
                    )
                except DataSourcesStompNotConnected:
                    logger.warning('Cant follow twin, stomp not currently connected')
                    break

                self._template_twin_dict.update({twin.id.value: twin.id.value})

                if subscription_id:
                    logger.info('Subscribed to feed on twin %s', twin.id.value)

    def _get_data_from_queue(self):
        api_to_call = self._data_to_fetch_queue.get()

        return api_to_call

    def _setup(self):
        """Create an twin and set its meta data. Create a feed an set its meta data."""

        logger.debug('Synthesiser setup')
        twin_id = self._create_twin()
        self._set_twin_meta(twin_id)

        feed_name = self._create_feed(twin_id)
        self._set_feed_meta(twin_id, feed_name)

        return twin_id, feed_name

    def _share_feed_data(self, twin_id: str, feed_name: str, api_data):
        non_encoded_data = {
            'data': api_data,
            'template_id': 'weather_forecast'
        }
        json_data = json.dumps(non_encoded_data)
        try:
            base64_encoded_data = base64.b64encode(json_data.encode()).decode()
        except TypeError as err:
            raise CallApiBaseException(
                f'Can not encode data to share from {twin_id}/{feed_name}: {err}, {json_data}'
            ) from err

        self.feed_api.share_feed_data(
            twin_id, feed_name,
            data=base64_encoded_data, mime='application/json',
            occurred_at=datetime.now(tz=timezone.utc).isoformat()
        )

        return non_encoded_data

    def publish(self, twin_id: str, feed_name: str, api_data):
        """Publish a new random temperature in Celsius."""

        try:
            non_encoded_data = self._share_feed_data(twin_id, feed_name, api_data)
        except DataSourcesQApiError as err:
            logger.error('Publishing QAPI error: %s', err, exc_info=is_enabled_for_debug())
        else:
            logger.info('Published %s', non_encoded_data)

    def run(self):
        logger.info('Synthesiser started')
        twin_id, feed_name = self._setup()

        while True:
            self.follow_twins()
            api_to_call = self._get_data_from_queue()

            if api_to_call:
                logger.info('api_to_call: %s', api_to_call)
                api_data = self._call_api(api_to_call)
                logger.info('api_data = %s', api_data)
                self.publish(twin_id, feed_name, api_data)


def run_follower():
    """Follower entry point called by the console script declared in the setup.cfg"""

    try:
        conf = CallApiConf.get_conf()
        logging.basicConfig(
            format='%(asctime)s %(levelname)s [%(name)s] {%(threadName)s} %(message)s', level=conf.root_log_level
        )
        agent_auth = AgentAuthBuilder.build_agent_auth(conf.auth.resolver_host, conf.auth.seed, conf.auth.user)
        qapi_factory = QApiFactory(conf, agent_auth, client_app_id=f'callapi_{uuid4()}')

        follower = CallApi(agent_auth, qapi_factory, conf.update_frequency_seconds)
        follower.run()
    except CallApiBaseException as err:
        logger.error('Follower error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesConfigurationError as err:
        logger.error('Configuration error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesError as err:
        logger.error('CallApi} error: %s', err, exc_info=is_enabled_for_debug())
    except Exception as err:  # pylint: disable=W0703
        logger.error('Unexpected error: %s', err, exc_info=is_enabled_for_debug())


if __name__ == '__main__':
    run_follower()
