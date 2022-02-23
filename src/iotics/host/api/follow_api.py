# Copyright 2022 Iotic Labs Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Iotic-Labs/iotics-host-lib/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from functools import partial
from time import sleep
from typing import Callable, Optional, Tuple

import shortuuid
from iotic.web.rest.client.qapi import FetchInterestResponse, FetchInterestResponsePayload, Headers
from iotic.web.stomp.client import StompWSConnection12
from retry import retry
from stomp import ConnectionListener
from stomp.exception import StompException

from iotics.host import metrics
from iotics.host.api.utils import deserialize, get_stomp_error_message
from iotics.host.auth import AgentAuth
from iotics.host.conf.base import DataSourcesConfBase
from iotics.host.exceptions import DataSourcesFollowTimeout, DataSourcesStompError, DataSourcesStompNotConnected

logger = logging.getLogger(__name__)


class FollowStompListener(ConnectionListener):
    # See more features in the ConnectionListener,
    # http://jasonrbriggs.github.io/stomp.py/
    # and https://stomp.github.io/stomp-specification-1.2.html
    def __init__(self, message_handler: Callable, disconnect_handler: Callable):
        self._message_handler = message_handler
        self._disconnect_handler = disconnect_handler
        self.regenerate_token = False
        self.receipts = set()
        self.errors = {}

    def clear(self):
        self.receipts = set()
        self.errors = {}

    def on_connected(self, headers: dict, body):
        logger.info('Stomp Follow connected %s, %s', headers, body)

    def on_disconnected(self):
        logger.warning('Stomp Follow disconnected')
        if self._disconnect_handler:
            logger.debug('Attempting reconnect in 1s')
            sleep(1)
            try:
                self._disconnect_handler()
            except Exception as ex:
                raise DataSourcesStompNotConnected(ex) from ex

    @staticmethod
    def to_interest_fetch_response(headers: dict, body) -> FetchInterestResponse:
        payload = deserialize(body, FetchInterestResponsePayload)
        headers = Headers(client_app_id=headers.get('Iotics-ClientAppId'),
                          client_ref=headers.get('Iotics-ClientRef'),
                          consumer_group=headers.get('Iotics-ConsumerGroup'),
                          request_timeout=headers.get('Iotics-RequestTimeout'),
                          transaction_ref=headers.get('Iotics-TransactionRef', '').split(','))
        return FetchInterestResponse(headers=headers, payload=payload)

    def on_message(self, headers: dict, body):
        destination = headers['destination']

        logger.debug('[On message] Destination: - %s', destination)

        try:
            deserialised_resp = self.to_interest_fetch_response(headers, body)
        except Exception as ex:  # pylint: disable=broad-except
            self.errors[headers['receipt-id']] = 'Deserialization error: %s' % ex
        else:
            self._message_handler(headers, deserialised_resp)

    def on_error(self, headers: dict, body):
        logger.error('Received stomp error body: %s headers: %s', body, headers)
        try:
            # This will be improved once https://ioticlabs.atlassian.net/browse/FO-1889 will be done
            error = get_stomp_error_message(body) or 'No error body'
            if error in (
                    'UNAUTHENTICATED: token expired', 'The connection frame does not contain valid credentials.'
            ):
                self.regenerate_token = True
        except Exception as ex:  # pylint: disable=broad-except
            error = 'Deserialization error: %s' % ex
        self.errors[headers['receipt-id']] = error

    def on_receipt(self, headers: dict, body):
        self.receipts.add(headers['receipt-id'])


class FollowAPI:
    def __init__(self, config: DataSourcesConfBase, agent_auth: AgentAuth, client_app_id: str,
                 reconnect_attempts_max: int = 10, heartbeats: Tuple[int, int] = (10000, 10000)):
        parametrized_connect = partial(self._connect, reconnect_attempts_max, heartbeats)
        self.active = True
        self.agent_auth = agent_auth
        self.client = None
        self.client_app_id = client_app_id
        self.listener = FollowStompListener(self._message_handler, parametrized_connect)
        self.stomp_url = config.qapi_stomp_url
        self._subscriptions = {}
        self.token = agent_auth.make_agent_auth_token()
        self.verify_ssl = config.verify_ssl
        try:
            parametrized_connect()
        except Exception as ex:
            raise DataSourcesStompNotConnected(ex) from ex

    @retry(exceptions=ConnectionError, delay=1, backoff=10, max_delay=3600)
    def _connect(self, reconnect_attempts_max: int, heartbeats: Tuple[int, int]):
        """this method also used to handle reconnecting to stomp server if e.g. network connection goes down
        """
        # Do not allow reconnect if disconnected for discard
        if not self.active:
            return

        logger.debug('Attempting stomp connection')
        self.client = StompWSConnection12(
            self.stomp_url, reconnect_attempts_max=reconnect_attempts_max, heartbeats=heartbeats
        )
        self.client.set_ssl(verify=self.verify_ssl)
        self.client.set_listener(f'{self.client_app_id} follow listener', self.listener)
        if self.listener.regenerate_token:
            self.token = self.agent_auth.make_agent_auth_token()
            self.listener.regenerate_token = False
        self.listener.clear()
        self.client.connect(wait=True, passcode=self.token)

        self._resubscribe_all()

    @metrics.add()
    def disconnect(self):
        """As there is no public reconnect method, this renders the instance inoperable.
        """
        self.active = False
        self.client.remove_listener(f'{self.client_app_id} follow listener')
        self.client.disconnect()

    def _resubscribe_all(self):
        """used on reconnect to resubscribe to all topics
        """
        for topic in self._subscriptions:
            _, sub_id = self._subscriptions[topic]
            headers = self._get_headers(sub_id)
            headers.update({'receipt': topic})
            self.client.subscribe(topic, id=sub_id, headers=headers)
            try:
                self._check_receipt(topic)
            except KeyError as ex:
                raise DataSourcesFollowTimeout('Did not get receipt subscribing to %s' % topic) from ex

    @retry(exceptions=KeyError, tries=100, delay=0.1, logger=None)
    def _check_receipt(self, topic: str):
        error = self.listener.errors.pop(topic, None)
        if error:
            raise DataSourcesStompError('Error subscribing to %s: %s' % (topic, error))

        self.listener.receipts.remove(topic)
        logger.debug('Successfully subscribed to %s', topic)

    def _get_headers(self, client_ref: str = None, transaction_ref: str = None):
        client_ref = client_ref or f'cref-{shortuuid.uuid()}'
        transaction_ref = transaction_ref or f'txref-{shortuuid.ShortUUID().random(length=10)}'
        logging.debug(f'Follow feed subscription headers: {client_ref} {transaction_ref}')  # pylint: disable=W1203
        return {'Iotics-ClientAppId': self.client_app_id,
                'Iotics-ClientRef': client_ref,
                'Iotics-TransactionRef': transaction_ref}

    def _message_handler(self, headers: dict, message):
        topic = headers['destination']

        try:
            callback, _ = self._subscriptions[topic]
        except KeyError:
            logger.warning('Received message for unsubscribed topic %s', topic)
            return
        try:
            metrics.measure(callback, headers['subscription'], message)
        except:  # noqa: E722 pylint: disable=W0702
            logger.exception('Callback error for topic %s', topic)
            return

    @metrics.add()
    def subscribe_to_feed(self, follower_twin_id: str, followed_twin_id: str, followed_feed_name: str,
                          callback: Callable, client_ref: str = None, transaction_ref: str = None,
                          remote_host_id: str = None) -> Optional[str]:
        """Subscribe to a twin's feed and provide a callable to be executed on its data when it is shared

        Args:
            follower_twin_id (str): The ID of the twin doing the following
            followed_twin_id (str): The ID of the twin whose feed is to be followed
            followed_feed_name (str): The ID of the feed to follow (unique per-twin)
            callback (Callable): A function to be executed on each feed share, taking the subscription header and the
                message as arguments
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char
            remote_host_id (str, optional): Set this to follow a feed on a remote host
        Returns:
            int: subscription id, or None if already subscribed

        """

        # this pattern for the subscribe topic:
        if remote_host_id:
            # '/qapi/twins/{consumer_entity_id}/interests/hosts/{followed_host_id}/twins/{followed_entity_id}/feeds/{followed_point_id}'  # noqa: E501 pylint: disable=C0301
            topic = f'/qapi/twins/{follower_twin_id}/interests/hosts/{remote_host_id}/twins/{followed_twin_id}/feeds/{followed_feed_name}'  # noqa: E501 pylint: disable=C0301
            logger.debug('Subscribing to remote feed')
        else:
            # "^/qapi/twins/(?<followerTwinId>.+)/interests/twins/(?<followedTwinId>.+)/feeds/(?<followedFeedId>.+)$"  # noqa: E501 pylint: disable=C0301
            topic = f'/qapi/twins/{follower_twin_id}/interests/twins/{followed_twin_id}/feeds/{followed_feed_name}'
            logger.debug('Subscribing to local feed')

        if topic in self._subscriptions:
            return None

        headers = self._get_headers(client_ref, transaction_ref)
        headers.update({'receipt': topic})
        subscription_id = headers['Iotics-ClientRef']

        try:
            self.client.subscribe(topic, id=subscription_id, headers=headers)
        except StompException as ex:
            raise DataSourcesStompNotConnected from ex
        try:
            self._check_receipt(topic)
        except KeyError as ex:
            raise DataSourcesFollowTimeout('Did not get receipt subscribing to %s' % topic) from ex

        self._subscriptions[topic] = (callback, subscription_id)

        return subscription_id


def get_follow_api(config: DataSourcesConfBase, agent_auth: AgentAuth, app_id: str = None) -> FollowAPI:
    app_id = app_id if app_id else f'follow_api_{str(shortuuid.uuid())}'
    return FollowAPI(config, agent_auth, client_app_id=app_id)
