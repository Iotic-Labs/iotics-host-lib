# Copyright © 2021 to 2022 IOTIC LABS LTD. info@iotics.com
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
from unittest.mock import MagicMock, patch
import pytest

from stomp.exception import NotConnectedException

from iotics.host.api.follow_api import FollowAPI, StompWSConnection12
from iotics.host.api.qapi import QApiFactory
from iotics.host.exceptions import DataSourcesStompError, DataSourcesStompNotConnected
from tests.iotics.data.mocks import AgentAuthTest, ConfTest, MockStompConnection


def test_should_get_a_follow_api():
    with patch('iotics.host.api.follow_api.StompWSConnection12'):
        api = QApiFactory(ConfTest(), AgentAuthTest()).get_follow_api()
    assert isinstance(api, FollowAPI)


def test_should_raise_error_if_stomp_not_connected():
    mock_disconnected_stomp = MagicMock()
    mock_disconnected_stomp.return_value.subscribe.side_effect = NotConnectedException()

    with patch('iotics.host.api.follow_api.StompWSConnection12', mock_disconnected_stomp):
        api = QApiFactory(ConfTest(), AgentAuthTest()).get_follow_api()
    with pytest.raises(DataSourcesStompNotConnected):
        api.subscribe_to_feed('foo', 'foo', 'foo', lambda: True)


class ErroringStompConnection(MockStompConnection):
    code = 2

    def subscribe(self, destination, headers=None, **kwargs):
        try:
            headers['receipt-id'] = headers.pop('receipt')
        except KeyError:
            pass
        self.listener.on_error(headers, '{"code":%d, "message": "Oh noes"}' % self.code)


class AuthExpiredStompConnection(ErroringStompConnection):
    code = 16


def test_should_raise_error_if_stomp_error():
    mock_auth = AgentAuthTest()
    conn = ErroringStompConnection()
    with patch('iotics.host.api.follow_api.StompWSConnection12', conn):
        api = QApiFactory(ConfTest(), mock_auth).get_follow_api()
    with pytest.raises(DataSourcesStompError):
        api.subscribe_to_feed('foo', 'foo', 'foo', lambda x: True)
    assert api.listener.regenerate_token is False
    assert mock_auth.make_agent_auth_token.call_count == 1
    with patch('iotics.host.api.follow_api.StompWSConnection12', conn):
        api.listener.on_disconnected()
    assert api.listener.regenerate_token is False
    assert mock_auth.make_agent_auth_token.call_count == 1


def test_should_require_new_token_if_401():
    mock_auth = AgentAuthTest()
    conn = AuthExpiredStompConnection()
    with patch('iotics.host.api.follow_api.StompWSConnection12', conn):
        api = QApiFactory(ConfTest(), mock_auth).get_follow_api()
    with pytest.raises(DataSourcesStompError):
        api.subscribe_to_feed('foo', 'foo', 'foo', lambda: True)
    assert api.listener.regenerate_token is True
    assert mock_auth.make_agent_auth_token.call_count == 1
    with patch('iotics.host.api.follow_api.StompWSConnection12', conn):
        api.listener.on_disconnected()
    assert api.listener.regenerate_token is False
    assert mock_auth.make_agent_auth_token.call_count == 2


def test_successful_reconnect():
    with patch('iotics.host.api.follow_api.StompWSConnection12', MockStompConnection()):
        api = QApiFactory(ConfTest(), AgentAuthTest()).get_follow_api()
        api.subscribe_to_feed('first', 'first', 'first', lambda: True)
        api.subscribe_to_feed('second', 'second', 'second', lambda: True)
        api.listener.on_error({'receipt-id': list(api._subscriptions)[0]}, 'foo')  # pylint: disable=protected-access
        api.listener.on_disconnected()  # will call the reconnect method, which should execute without error


def test_api_disconnect_idempotence():
    def _stomp_connected(self, **kwargs):
        self.connected = True

    with patch.object(StompWSConnection12, 'connect', autospec=True, side_effect=_stomp_connected):
        with patch('iotic.web.stomp.client.WSTransport'):
            with patch.object(FollowAPI, '_check_receipt'):
                api = QApiFactory(ConfTest(), AgentAuthTest()).get_follow_api()

    api.disconnect()
    api.disconnect()
