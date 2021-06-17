import base64
import json
import logging
from time import sleep
from uuid import uuid4
from collections import namedtuple
from typing import List
import datetime as dt
import geopy.distance
from iotic.web.rest.client.qapi import ModelProperty, Uri, StringLiteral, LangLiteral, Value
from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder, AgentAuth
from iotics.host.exceptions import (
    DataSourcesConfigurationError, DataSourcesError, DataSourcesSearchTimeout,
    DataSourcesStompError, DataSourcesStompNotConnected, DataSourcesQApiError
)

from pollentrainsynth.exceptions import PollenTrainSynthesiserBaseException
from pollentrainsynth.conf import PollenTrainSynthesiserConf

logger = logging.getLogger(__name__)
# turn down stomp logging
logging.getLogger('stomp.py').setLevel(level=logging.ERROR)

POLLEN_INFO = 'pollen'
POLLEN_FEED_VALUES = [
    Value(
        label='amount',
        data_type='decimal',
        comment='Pollen amount',
        unit='https://www.aqua-calc.com/what-is/density/grain-per-cubic-meter'
    )
]

POLLEN_PROPERTY = [ModelProperty(
    key='http://data.iotics.com/ns/category',
    uri_value=Uri(value='http://data.iotics.com/category/environment/Pollen')
), ModelProperty(
    key='http://data.iotics.com/ns/category',
    uri_value=Uri(value='http://data.iotics.com/category/Environment')
)]

RRPS_ONT_PREFIX = 'http://www.mtu-solutions.com/ont/'
ENGINE_DEFINITION_PROPERTIES = [ModelProperty(
    key='http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    uri_value=Uri(value=f'{RRPS_ONT_PREFIX}Engine')
)]

TRAIN_TWIN_SHARE_TIME_LIMIT = 120

def is_enabled_for_debug():
    return logger.isEnabledFor(logging.DEBUG)


class PollenTrainSynthesiser:

    def __init__(self, agent_auth_f: AgentAuth, qapi_factory_f: QApiFactory, agent_auth_p: AgentAuth, qapi_factory_p: QApiFactory, update_frequency_seconds: float):
        self.twin_api_f = qapi_factory_f.get_twin_api()
        self.search_api_f = qapi_factory_f.get_search_api()
        self.follow_api = qapi_factory_f.get_follow_api()
        self.interest_api = qapi_factory_f.get_interest_api()
        self.twin_api_p = qapi_factory_p.get_twin_api()
        self.feed_api = qapi_factory_p.get_feed_api()
        self.agent_auth_f = agent_auth_f
        self.agent_auth_p = agent_auth_p
        self.engine_feed_twin_map = {}
        self.pollen_twin_feeds = {}
        self.train_id_lookup = {} # Lookup table used to keep track of Twin IDs
        self.loop_time = update_frequency_seconds
        self.follower_twin_id = None

    def create_follower_twin(self):
        twin_id, _, _ = self.agent_auth_f.make_twin_id('PollenTrainSynthesiser')
        self.twin_api_f.create_twin(twin_id)
        self.follower_twin_id = twin_id

    def _create_twin(self, twin_name: str, train_id: str) -> tuple:
        twin_id, _, _ = self.agent_auth_p.make_twin_id(twin_name)
        logger.debug('Creating twin %s - %s', twin_id, twin_name)
        self.twin_api_p.create_twin(twin_id)
        self.twin_api_p.update_twin(twin_id, add_props=self._get_properties(train_id), clear_all_props=True)

        return twin_id

    #work on this at end
    @staticmethod
    def follow_callback(header, body):  # pylint: disable=W0613
        decoded_data = base64.b64decode(body.payload.feed_data.data).decode('ascii')
        pollen_data = json.loads(decoded_data)
        print(pollen_data)
        timestamp = body.payload.feed_data.occurred_at.isoformat()

        logger.info('Received pollen data %s at time %s', pollen_data, timestamp)

    def follow_engine_callback(self,header, body):  # pylint: disable=W0613
        decoded_data = base64.b64decode(body.payload.feed_data.data).decode('ascii')
        twin_id = body.payload.interest.followed_feed.twin_id.value
        location = json.loads(decoded_data)
        print(header)
        timestamp = body.payload.feed_data.occurred_at
        time_diff = dt.datetime.now(tz=dt.timezone.utc) - timestamp
        print(time_diff)
        # date_today = str(dt.date.today())
        # if time_diff.seconds >= TRAIN_TWIN_SHARE_TIME_LIMIT:
        #     print('twin already exist preparing to update feed')
            
        #     feed_data,last_pollen_share_time = self._setup_feed_data(location)
            
        #     if date_today in last_pollen_share_time and feed_data.get('max_pollen_count') > last_max_pollen:
        #         feed_time = self._share_feed_data(published_twin_id, location)
        #         self.train_id_lookup[train_id]['last_share_time'] = feed_time

        logger.info('Received engine data %s at time %s', location, timestamp)

    @staticmethod
    def _extract_property_values(twin):
        properties = {}

        for prop in twin.properties:
            if prop.key == f'{RRPS_ONT_PREFIX}engine_id':
                properties['engine_id'] = prop.string_literal_value.value
            elif prop.key == f'{RRPS_ONT_PREFIX}train_id':
                properties['train_id'] = prop.string_literal_value.value
            elif prop.key == f'{RRPS_ONT_PREFIX}car_number':
                properties['car_number'] = prop.string_literal_value.value

        return properties

    @staticmethod
    def _get_properties(train_id):
        # TODO: This does not represent the real ontology  # pylint: disable=W0511
        ret = [ModelProperty(
            key=f'{RRPS_ONT_PREFIX}train_id',
            string_literal_value=StringLiteral(value=train_id)
        ), ModelProperty(
            key='http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
            uri_value=Uri(value=f'{RRPS_ONT_PREFIX}Train')
        )]

        return ret

    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2):

        return geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).km

    def get_most_recent_data(self, followed_twin_id: str, feed_id: str):
        """ Get feed's most recent data via the InterestApi
            Note: the feed metadata must include store_last=True
        """
        logger.info('Get most recent data via InterestApi')
        most_recent_data = self.interest_api.get_feed_last_stored_local(
            follower_twin_id=self.follower_twin_id,
            followed_twin_id=followed_twin_id,
            feed_id=feed_id
        )
        
        if not most_recent_data.feed_data:
            logger.info('No most recent data found.')
            return None, None
        share_time = most_recent_data.feed_data.occurred_at
        decoded_data = base64.b64decode(most_recent_data.feed_data.data).decode()
        recent_data = json.loads(decoded_data)
        logger.info('Most recent data %s, %s', recent_data, share_time)
        return recent_data, share_time

    # def _get_last_remote_value(self, interest_api, host_id, follower_twin_id,
    #     followed_twin_id, # the twin you want to follow
    #     feed_id):
    #     most_recent_data = interest_api.get_feed_last_stored(
    #         self, host_id, follower_twin_id, followed_twin_id, feed_id
    #     )
    #     if not most_recent_data.feed_data:
    #         return
    #     share_time = most_recent_data.feed_data.occurred_at
    #     decoded_data = base64.b64decode(most_recent_data.feed_data.data).decode()
    #     data = json.loads(decoded_data)

    def follow_pollen_twins(self):
        """Find and follow twins"""
        search_resp_gen = None
        logger.info('Searching for twins.')
        try:
            # search for twins
            # note: a generator is returned because responses are yielded
            # as they come in asynchronously from the network of hosts
            search_resp_gen = self.search_api_f.search_twins(properties=POLLEN_PROPERTY, scope='GLOBAL')
        except DataSourcesSearchTimeout as timeout_ex:
            logger.warning('Timed out searching for twins: %s', timeout_ex)
        except DataSourcesStompError as ex:
            logger.error('Error searching for twins: %s', ex)
        except DataSourcesStompNotConnected:
            logger.warning('Cant search for twins, stomp not currently connected')

        if not search_resp_gen:
            logger.info('No twins found')
            return

        found_twins = 0
        subscription_count = 0
        for search_resp in search_resp_gen:

            for twin in search_resp.twins:
                found_twins += 1
                feed_info_list = twin.feeds
                if not feed_info_list:
                    logger.warning('No feeds available')
                    break
                try:
                    # follow twin's feed
                    subscription_id = self.follow_api.subscribe_to_feed(
                        self.follower_twin_id, twin.id.value, 'pollen_amount_0_24h', self.follow_callback
                    )
                    print(twin.id.value)
                    print(self.pollen_twin_feeds.get(twin.id.value))
                    if not self.pollen_twin_feeds.get(twin.id.value):
                        pollen_temp_twin = {
                            'lat': twin.location.lat,
                            'long': twin.location.lon,
                            'temp_distance': 0,
                            'pollen_amount': 0,
                            'last_update': None
                        }
                        self.pollen_twin_feeds.update({twin.id.value: pollen_temp_twin})
                except DataSourcesStompNotConnected:
                    logger.warning('Cant follow twin, stomp not currently connected')

                if subscription_id:
                    subscription_count += 1
                    logger.info('Subscribed to feed on twin %s', twin.id.value)
                    # Optional call to get the feed's most recent data via the InterestApi
                    # This call is not needed to perform a follow
                    pollen_feed_data, last_update = self.get_most_recent_data(twin.id.value, 'pollen_amount_0_24h')
                    if pollen_feed_data:
                        self.pollen_twin_feeds[twin.id.value]['pollen_amount'] = pollen_feed_data.get('amount')
                        self.pollen_twin_feeds[twin.id.value]['last_update'] = last_update
        logger.info('Found %s twins; subscribed to %s new feeds.', found_twins, subscription_count)

    def follow_engines(self):
        """ Find and follow engines
        """
        search_responses = None
        

        try:
            search_responses = self.search_api_f.search_twins(properties=ENGINE_DEFINITION_PROPERTIES)

        except DataSourcesSearchTimeout as timeout_ex:
            logger.warning('Timed out searching for twins: %s', timeout_ex)
        except DataSourcesStompError as ex:
            logger.error('Error searching for twins: %s', ex)
        except DataSourcesStompNotConnected:
            logger.warning('Cant search for engines, stomp not currently connected')

        if not search_responses:
            logger.info('No engines found.')
            return

        found_count = 0

        for response in search_responses:
            if found_count == 15:
                break
            for twin in response.twins:
                if found_count == 15:
                    break
                found_count += 1
                
                valid_twin_id = twin.id.value  # unused value

                try:
                    subscription_id = self.follow_api.subscribe_to_feed(
                        valid_twin_id, twin.id.value, 'Location', self.follow_engine_callback
                    )
                except DataSourcesStompNotConnected:
                    logger.warning('Cant follow engines, stomp not currently connected')
                    break
                
                

                if subscription_id:
                    logger.info('Subscribed to feed on twin %s', twin.id.value)
                    self.engine_feed_twin_map.update({str(subscription_id): self._extract_property_values(twin)})
                    twin_prop = self._extract_property_values(twin)
                    location, last_engine_share = self.get_most_recent_data( twin.id.value, 'Location')
                    print('engine last update_time %s', last_engine_share)
                    if not location:
                        continue
                    train_id = twin_prop.get('train_id')
                    published_twin_id = None
                    train_info = self.train_id_lookup.get(train_id)
                    if train_info:
                        published_twin_id = train_info.get('twin_id')
                        last_shared_time = dt.datetime.fromisoformat(train_info.get('last_share_time'))
                        last_max_pollen = train_info.get('pollen_amount')
                    if not published_twin_id:
                        print('creating twin and  updating feed')
                        feed_data,last_pollen_share_time = self._setup_feed_data(location)
                        published_twin_id = self._create_trains_twins(train_id)
                        if location:
                            feed_time = self._share_feed_data(published_twin_id, location)
                            self.train_id_lookup[train_id]['last_share_time'] = feed_time
                            self.train_id_lookup[train_id]['pollen_amount'] = feed_data.get('max_pollen_count')
                        continue
                    time_diff = dt.datetime.now(tz=dt.timezone.utc) - last_shared_time
                    print(time_diff)
                    if time_diff.seconds >= TRAIN_TWIN_SHARE_TIME_LIMIT:
                        print('twin already exist preparing to update feed')
                        
                        feed_data,last_pollen_share_time = self._setup_feed_data(location)
                        
                        if date_today in last_pollen_share_time and feed_data.get('max_pollen_count') > last_max_pollen:
                            feed_time = self._share_feed_data(published_twin_id, location)
                            self.train_id_lookup[train_id]['last_share_time'] = feed_time
                    

        logger.debug('Found %s engine(s)', found_count)
        

    def _create_trains_twins(self, train_id):
        twin_name = f'''train_{train_id}'''
        twin_id = self._create_twin(twin_name, train_id)
        twin_info = {
            'train_id': train_id,
            'last_share_time': None,
            'pollen_amount': 0
        }
        self.train_id_lookup.update({twin_id: twin_info})
        # logger.info('Train twin created %s!', twin_id)
        self._create_feed(twin_id)
        return twin_id
        # for key, value in self.engine_feed_twin_map.items():
        #     train_id = value.get('train_id')
        #     twin_id = self.train_id_lookup.get(train_id)
        #     print(twin_id)
        #     if not twin_id:
        #         twin_name = f'''train_{train_id}'''
        #         twin_id = self._create_twin(twin_name, train_id)
        #         self.train_id_lookup.add(train_id, twin_id)
        #         self._create_feed(twin_id)
        #     feed_data = self._share_feed_data(twin_id)

        #logger.info('Train twins created !')
        
    
    def _create_feed(self, twin_id: str):

        # Create feed on pollen info 
        feed_label = 'Train Twin'
        feed_desc = 'Train twin for pollen data'

        feed_id = self.feed_api.create_feed(twin_id, POLLEN_INFO)
        self.feed_api.update_feed(
            twin_id,
            POLLEN_INFO,
            add_labels=[LangLiteral(value=feed_label, lang='en')],
            add_comments=[LangLiteral(value=feed_desc, lang='en')],
            store_last=True,
            add_values=POLLEN_FEED_VALUES
        )


    def _setup_feed_data(self, location):
        """Sets up and returns non-encoded feed data to be shared"""
        # get max pollen from the nearby available pollen threshold location.
        try:
            for key, value in self.pollen_twin_feeds.items():
                distance  = self._calculate_distance(value.get('lat'),value.get('long'), location.get('Latitude'), location.get('Longitude'))
                self.pollen_twin_feeds[key]['temp_distance'] = distance
            pollen_key = (min(self.pollen_twin_feeds, key=lambda x: self.pollen_twin_feeds[x]['temp_distance']))
            min_distance = self.pollen_twin_feeds[pollen_key]['temp_distance']
            max_pollen_count = self.pollen_twin_feeds[pollen_key]['pollen_amount']
            last_shared_time = self.pollen_twin_feeds[pollen_key]['last_update'] 
            for key, value in self.pollen_twin_feeds.items():
                if value.get('temp_distance') == min_distance and max_pollen_count < value.get('pollen_amount'):
                    max_pollen_count = value.get('pollen_amount')
                    last_shared_time = value.get('last_shared_time')
                    self.pollen_twin_feeds[key]['pollen_amount'] += 1

            feed_data = {
                'max_pollen_count': max_pollen_count
            }

            return feed_data, last_shared_time.isoformat()
        except AttributeError as err:
            print(err, value.get('lat'),value.get('long'), location.get('Latitude'), location.get('Longitude'))
            return None, None

    def _share_feed_data(self,twin_id, feed_data):
        """Shares data of a created feed"""

        
        json_data = json.dumps(feed_data)
        base64_encoded_data = base64.b64encode(json_data.encode()).decode()  # Encode feed data to base64
        try:
            occurred_at = dt.datetime.now(tz=dt.timezone.utc).isoformat()
            self.feed_api.share_feed_data(
                twin_id, POLLEN_INFO,
                data=base64_encoded_data, mime='application/json',
                occurred_at=occurred_at  # Timestamp of data shared
            )
            return occurred_at

        except DataSourcesQApiError as err:
            logger.error('Publishing QAPI error: %s', err, exc_info=is_enabled_for_debug())

        return feed_data

    def run(self):
        #logger.info('Follower started')
        self.create_follower_twin()

        while True:
            self.follow_pollen_twins()
            self.follow_engines()
            logger.info('Sleeping for %s seconds', self.loop_time)
            sleep(self.loop_time)


def run_follower():
    """Follower entry point called by the console script declared in the setup.cfg"""

    # try:
    conf_f = PollenTrainSynthesiserConf.get_conf_f()
    conf_p = PollenTrainSynthesiserConf.get_conf_p()
    logging.basicConfig(
        format='%(asctime)s %(levelname)s [%(name)s] {%(threadName)s} %(message)s', level=conf_f.root_log_level
    )
    agent_auth_f = AgentAuthBuilder.build_agent_auth(conf_f.auth.resolver_host, conf_f.auth.seed, conf_f.auth.user)
    qapi_factory_f = QApiFactory(conf_f, agent_auth_f, client_app_id=f'pollentrainsynth_{uuid4()}')
    agent_auth_p = AgentAuthBuilder.build_agent_auth(conf_p.auth.resolver_host, conf_p.auth.seed, conf_p.auth.user)
    qapi_factory_p = QApiFactory(conf_p, agent_auth_p, client_app_id=f'pollentrainsynth_{uuid4()}')

    follower = PollenTrainSynthesiser(agent_auth_f, qapi_factory_f, agent_auth_p, qapi_factory_p, conf_f.update_frequency_seconds)
    follower.run()
    # except PollenTrainSynthesiserBaseException as err:
    #     logger.error('Follower error: %s', err, exc_info=is_enabled_for_debug())
    # except DataSourcesConfigurationError as err:
    #     logger.error('Configuration error: %s', err, exc_info=is_enabled_for_debug())
    # except DataSourcesError as err:
    #     logger.error('PollenTrainSynthesiser} error: %s', err, exc_info=is_enabled_for_debug())
    # except Exception as err:  # pylint: disable=W0703
    #     logger.error('Unexpected error: %s', err, exc_info=is_enabled_for_debug())


if __name__ == '__main__':
    run_follower()
