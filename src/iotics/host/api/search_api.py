from collections import defaultdict
from functools import partial
import json
import logging
from queue import Empty, Queue
import time
from typing import Callable, Generator, Tuple
from threading import Lock

import shortuuid
from iotic.web.rest.client.qapi import GeoCircle, GeoLocation, ModelProperty, PayloadFilter, ResponseType, Scope, \
    SearchRequestPayload, SearchResponsePayload, SearchResponseTwinDetails
from iotic.web.stomp.client import StompWSConnection12
from retry import retry
from stomp import ConnectionListener
from stomp.exception import StompException

from iotics.host.api.utils import deserialize, ListOrTuple, sanitize_for_serialization
from iotics.host.auth import AgentAuth
from iotics.host.conf.base import DataSourcesConfBase
from iotics.host.exceptions import DataSourcesQApiError, DataSourcesSearchTimeout, DataSourcesStompError, \
    DataSourcesStompNotConnected

logger = logging.getLogger(__name__)

TXREF_HEADER = 'Iotics-TransactionRef'
PAGE_LENGTH = 100


class ResultsQueue(Queue):
    def __init__(self):
        self.responses = 0
        super().__init__()


class SearchStompListener(ConnectionListener):
    def __init__(self, disconnect_handler: Callable):
        self.searches = {}
        self.results = defaultdict(ResultsQueue)
        self.receipts = set()
        self.errors = defaultdict(list)
        self.regenerate_token = False
        self._disconnect_handler = disconnect_handler
        self.page_lock = Lock()

    def clear(self):
        self.searches = {}
        self.results = defaultdict(ResultsQueue)
        self.receipts = set()
        self.errors = defaultdict(list)

    def on_message(self, headers: dict, body):
        tx_ref, page = headers[TXREF_HEADER].split('_page')
        page = int(page or 0)
        try:
            response = deserialize(body, SearchResponsePayload)
            assert isinstance(response.twins, list), 'Response does not have twins list'
        except Exception as ex:  # pylint: disable=broad-except
            self.errors[tx_ref].append('Deserialization error: %s' % ex)
        else:
            results = self.results[tx_ref]
            results.responses += 1
            for entity in response.twins:
                results.put(entity)
            if len(response.twins) >= PAGE_LENGTH:
                with self.page_lock:
                    search_function, last_page = self.searches[tx_ref]
                    if page == last_page:
                        search_function(page=page + 1)
                        self.searches[tx_ref] = search_function, page + 1

    def on_receipt(self, headers: dict, body):
        self.receipts.add(headers['receipt-id'])

    def on_error(self, headers: dict, body):
        logger.error('Received search stomp error body: %s headers: %s', body, headers)
        try:
            # This will be improved once https://ioticlabs.atlassian.net/browse/FO-1889 will be done
            error = json.loads(body).get('error', 'No error body')
            if error in (
                    'UNAUTHENTICATED: token expired', 'The connection frame does not contain valid credentials.'
            ):
                self.regenerate_token = True
        except Exception as ex:  # pylint: disable=broad-except
            error = 'Deserialization error: %s' % ex
        tx_ref, _ = headers[TXREF_HEADER].split('_page')
        self.errors[tx_ref].append(error)

    def on_connected(self, headers: dict, body):
        logger.info('Stomp Search connected %s, %s', headers, body)

    def on_disconnected(self):
        logger.warning('Stomp Search disconnected')
        if self._disconnect_handler:
            logger.debug('Attempting reconnect')
            self._disconnect_handler()


class SearchAPI:
    sub_topic = '/qapi/searches/results'
    dispatch_topic = '/qapi/searches/dispatches'

    def __init__(self, config: DataSourcesConfBase, agent_auth: AgentAuth, client_app_id: str,
                 reconnect_attempts_max: int = 10, heartbeats: Tuple[int, int] = (10000, 10000)):
        parametrized_connect = partial(self._connect, reconnect_attempts_max, heartbeats)
        self.active = True
        self.agent_auth = agent_auth
        self.client = None
        self.client_app_id = client_app_id
        self.listener = SearchStompListener(parametrized_connect)
        self.stomp_url = config.qapi_stomp_url
        self._subscribe_headers = dict(**self._get_headers(), receipt=self.sub_topic)
        self.token = agent_auth.make_agent_auth_token()
        self.verify_ssl = config.verify_ssl
        parametrized_connect()

    def _connect(self, reconnect_attempts_max: int, heartbeats: Tuple[int, int]):
        """also used to handle reconnecting to stomp server if e.g. network connection goes down
        """
        # Do not allow reconnect if disconnected for discard
        if not self.active:
            return

        self.client = StompWSConnection12(
            self.stomp_url, reconnect_attempts_max=reconnect_attempts_max, heartbeats=heartbeats
        )
        self.client.set_ssl(verify=self.verify_ssl)
        self.client.set_listener(f'{self.client_app_id} search listener', self.listener)
        if self.listener.regenerate_token:
            self.token = self.agent_auth.make_agent_auth_token()
        self.listener.clear()
        self.client.connect(wait=True, passcode=self.token)
        self.client.subscribe(self.sub_topic, id='search_subid', headers=self._subscribe_headers)
        self._check_receipt(self.sub_topic)
        self.listener.regenerate_token = False

    def disconnect(self):
        """As there is no public reconnect method, this renders the instance inoperable.
        """
        self.active = False
        self.client.remove_listener(f'{self.client_app_id} search listener')
        self.client.disconnect()

    @retry(exceptions=KeyError, tries=100, delay=0.1)
    def _check_receipt(self, topic: str):
        error = self.listener.errors.pop(topic, None)
        if error:
            raise DataSourcesStompNotConnected('Error subscribing to %s: %s' % (topic, error))

        self.listener.receipts.remove(topic)

    def _get_headers(self, tx_ref: str = None):
        client_ref = f'cref-{shortuuid.uuid()}'
        tx_ref = tx_ref or f'txref-{shortuuid.ShortUUID().random(length=10)}'
        logger.debug(f'Search feed subscription headers: {client_ref} {tx_ref}')  # pylint: disable=W1203
        return {'Iotics-ClientAppId': self.client_app_id,
                'Iotics-ClientRef': client_ref,
                TXREF_HEADER: tx_ref}

    def search_twins(
            self, timeout: int = 10, response_type: ResponseType = ResponseType.FULL, radius_km: float = None,
            lat: float = None, long: float = None, properties: ListOrTuple[ModelProperty] = None, text: str = None,
            scope: str = Scope.GLOBAL
    ) -> Generator[SearchResponseTwinDetails, None, None]:
        """Search for twins matching the given criteria. Note that argument descriptions reference possibility of
        providing a language parameter to the qapi, which is not currently offered by this method.

        Args:
            timeout (int, optional): How many seconds to search for (default 10)
            response_type (ResponseType, optional): Which data to return for each result, choices are:
                FULL (default): including twin and feed identifiers, labels/comments (for all languages if no language
                    provided), properties and location. TODO: Comments not mentioned in docs for return type
                LOCATED: including twin identifiers, location and label (for the provided language or default)
                MINIMAL:  including twins identifier only.
            radius_km (float, optional): How far from the given coordinates to return twins. Must be used with lat/long
            lat (float, optional): The latitude at the centre of the search radius. Must be used with radius_km and long
            long (float, optional): The longitude at the centre of the search radius. Must be used with radius_km & lat
            properties (list/tuple[ModelProperty], optional): Semantic properties which must all be present on the twins
                key (str): The predicate of the property. Then, one of the following value (object) types:
                lang_literal_value (LangLiteral), A string w/ language:
                    lang (str): 2-character language code
                    value (str): the text content of the property's object
                literal_value (Literal), Describes a non-string typed value:
                    data_type (str): short-form xsd type, eg 'integer', 'boolean'
                    value (str): Content of the value as a string
                string_literal_value (StringLiteral): Describes a string w/o language. One attribute, `value` (str)
                uri_value (Uri): One attribute, `value`, a string representing a URI
            text (str, optional): One or more keywords which must match either text from twin/feed labels/comments
                (in the given language). Note that any (rather than all) of the keywords will produce a match.
            scope (Scope, optional): Either LOCAL (default) to only return twins from the local host, or GLOBAL to
                return twins from anywhere on the network.

        Returns: Generator[SearchResponseTwinDetails, None, None]. Each item has this structure:
            feeds (list[SearchResponseFeedDetails]) - included in ResponseType.FULL, the feeds present on the twin:
                feed (Feed):
                    id (FeedID): has sole attribute `value`, containing the feed's ID as a string
                    twin_id (TwinID): has sole attribute `value`, containing the twin's ID as a string (redundant?)
                label (str): The feed human readable label in the language specified in the request (if set)
                store_last (bool): Whether you can access the last data shared to this feed via the InterestApi
            id (TwinID): has sole attribute `value`, containing the twin's ID as a string (redundant?)
            label (str): Twin human readable label in the language specified in the request (if set). Included with
                response_type FULL and LOCATED
            location (GeoLocation) - The coordinates of the non-digital twin:
                lat (float): latitude
                lon (float): longitude
            properties (list[ModelProperty]) - The custom semantic properties added to the twin. See args for structure.
                Included with response type FULL
            tags (list[str]): Any tags added to the twin. Included with response type FULL

        """
        if not any(val is not None for val in [radius_km, lat, long]):
            location_filter = None
        elif not all(val is not None for val in [radius_km, lat, long]):
            raise DataSourcesQApiError('Either all or none of radius_km, lat, and long must be set.')
        else:
            location_filter = GeoCircle(radius_km=radius_km, location=GeoLocation(lat=lat, lon=long))

        payload = SearchRequestPayload(response_type=response_type, filter=PayloadFilter(
            location=location_filter, properties=properties, text=text))

        tx_ref = f'txref-{shortuuid.ShortUUID().random(length=10)}'
        timeout_end = time.monotonic() + timeout
        search_function = partial(self._get_results_page, payload, tx_ref, timeout_end, scope)
        self.listener.searches[tx_ref] = search_function, 0
        search_function(page=0)

        def get_result():
            results = self.listener.results[tx_ref]
            while True:
                try:
                    result = results.get(timeout=max(timeout_end - time.monotonic(), 0))
                except Empty:
                    if results.responses:  # We ignore errors if any host has returned successfully
                        break
                    errors = self.listener.errors[tx_ref]
                    if errors:
                        raise DataSourcesStompError(errors[0])  # pylint: disable=raise-missing-from
                    raise DataSourcesSearchTimeout()  # pylint: disable=raise-missing-from

                yield result

        return get_result()

    def _get_results_page(
        self, payload: SearchRequestPayload, tx_ref: str, timeout_end: float, scope: str = Scope.GLOBAL, page: int = 0
    ):
        """
        Search for twins and return results from a given page, ie, from an offset of the page number times the maximum
        results per page
        """

        # no-op if this search's timeout has been reached.
        if time.monotonic() > timeout_end:
            return

        search_headers = self._get_headers(f'{tx_ref}_page{page}')
        search_headers.update({'scope': scope, 'limit': PAGE_LENGTH, 'offset': PAGE_LENGTH * page})
        try:
            self.client.send(
                self.dispatch_topic, headers=search_headers,
                body=json.dumps(sanitize_for_serialization(payload))
            )
        except StompException as ex:
            raise DataSourcesStompNotConnected from ex


def get_search_api(config: DataSourcesConfBase, agent_auth: AgentAuth, app_id: str = None) -> SearchAPI:
    app_id = app_id if app_id else f'search_api_{str(shortuuid.uuid())}'
    return SearchAPI(config, agent_auth, client_app_id=app_id)
