import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from stomp.exception import NotConnectedException

from iotics.host.api.qapi import QApiFactory
from iotics.host.api.search_api import SearchAPI, SearchStompListener, StompWSConnection12, TXREF_HEADER
from iotics.host.exceptions import (
    DataSourcesQApiError, DataSourcesSearchTimeout, DataSourcesStompError, DataSourcesStompNotConnected
)
from tests.iotics.data.mocks import AgentAuthTest, ConfTest, MockStompConnection

RESULT_ID = 'did:iotics:iotAd6upprAUjEtzoNVjnpiytNfx9YzK7Th3'


class _SearchResultStompConnection(MockStompConnection):
    def send(self, url, headers, body):
        self.listener.on_message(headers, json.dumps({'twins': [{'id': {'value': RESULT_ID}}]}))


@pytest.fixture
def api():
    with patch('iotics.host.api.search_api.StompWSConnection12', MockStompConnection()):
        return QApiFactory(ConfTest(), AgentAuthTest()).get_search_api()


@pytest.fixture
def mock_connected_api():
    def _stomp_connected(self, **kwargs):
        self.connected = True

    with patch.object(StompWSConnection12, 'connect', autospec=True, side_effect=_stomp_connected):
        with patch('iotic.web.stomp.client.WSTransport'):
            with patch.object(SearchAPI, '_check_receipt'):
                return QApiFactory(ConfTest(), AgentAuthTest()).get_search_api()


def test_should_get_a_search_api(api):
    assert isinstance(api, SearchAPI)


def test_should_raise_error_if_stomp_not_connected():
    mock_disconnected_stomp = MockStompConnection()
    mock_disconnected_stomp.return_value.send.side_effect = NotConnectedException()

    with patch('iotics.host.api.search_api.StompWSConnection12', mock_disconnected_stomp):
        api = QApiFactory(ConfTest(), AgentAuthTest()).get_search_api()
    with pytest.raises(DataSourcesStompNotConnected):
        api.search_twins()


@pytest.mark.parametrize('search_options', (
    {'radius_km': 10.0, 'lat': 0},
    {'radius_km': 10.0, 'long': 0},
    {'lat': 0, 'long': 0},
))
def test_should_raise_qapi_error_if_invalid_data(api, search_options):
    with pytest.raises(DataSourcesQApiError):
        api.search_twins(**search_options)


class ErroringStompConnection(MockStompConnection):
    error = 'foo'

    def send(self, url, headers, body):
        try:
            headers['receipt-id'] = headers.pop('receipt')
        except KeyError:
            pass
        self.listener.on_error(headers, '{"error":"%s"}' % self.error)


class AuthExpiredStompConnection(ErroringStompConnection):
    error = 'UNAUTHENTICATED: token expired'


def test_should_raise_error_if_stomp_error():
    mock_auth = AgentAuthTest()
    conn = ErroringStompConnection()
    with patch('iotics.host.api.search_api.StompWSConnection12', conn):
        api = QApiFactory(ConfTest(), mock_auth).get_search_api()
    with pytest.raises(DataSourcesStompError):
        list(api.search_twins(timeout=1))
    assert api.listener.regenerate_token is False
    assert mock_auth.make_agent_auth_token.call_count == 1
    with patch('iotics.host.api.search_api.StompWSConnection12', conn):
        api.listener.on_disconnected()
    assert api.listener.regenerate_token is False
    assert mock_auth.make_agent_auth_token.call_count == 1


def test_should_require_new_token_if_401():
    mock_auth = AgentAuthTest()
    conn = AuthExpiredStompConnection()
    with patch('iotics.host.api.search_api.StompWSConnection12', conn):
        api = QApiFactory(ConfTest(), mock_auth).get_search_api()
    with pytest.raises(DataSourcesStompError):
        list(api.search_twins(timeout=1))
    assert api.listener.regenerate_token is True
    assert mock_auth.make_agent_auth_token.call_count == 1
    with patch('iotics.host.api.search_api.StompWSConnection12', conn):
        api.listener.on_disconnected()
    assert api.listener.regenerate_token is False
    assert mock_auth.make_agent_auth_token.call_count == 2


def test_should_raise_error_if_search_timeouts_with_no_results(api):
    with pytest.raises(DataSourcesSearchTimeout):
        # Triggered by the `timeout` set on a queue.
        list(api.search_twins(timeout=1))


def test_should_not_try_to_get_another_result_page_after_timeout_reached():
    """Complementary test for code coverage (`test_should_raise_error_if_search_timeouts_with_no_results`)."""
    with patch('iotics.host.api.search_api.StompWSConnection12', _SearchResultStompConnection()):
        api = QApiFactory(ConfTest(), AgentAuthTest()).get_search_api()
    with pytest.raises(DataSourcesSearchTimeout):
        # Triggered by the `timeout_end` set in `_get_results_page` (to avoid search query after timeout).
        list(api.search_twins(timeout=0))  # Timeout 0 will never yield any results


def test_successful_search():
    with patch('iotics.host.api.search_api.StompWSConnection12', _SearchResultStompConnection()):
        api = QApiFactory(ConfTest(), AgentAuthTest()).get_search_api()
    # Range and location arguments added for code coverage - actual functionality cannot be tested by unit tests.
    results = api.search_twins(timeout=1, radius_km=10.0, lat=0, long=0)
    assert next(results).twins[0].id.value == RESULT_ID
    with pytest.raises(StopIteration):
        next(results)


def test_api_disconnect_idempotence(mock_connected_api):
    api = mock_connected_api
    api.disconnect()
    api.disconnect()


def test_api_disconnect_reconnect(mock_connected_api):
    api = mock_connected_api
    assert api.active
    # OSError - raised if tests are run in a Docker container:
    # https://medium.com/it-dead-inside/docker-containers-and-localhost-cannot-assign-requested-address-6ac7bc0d042b
    with pytest.raises((ConnectionRefusedError, OSError)):
        # Tries to reconnect and raises an error since no real connection is set.
        api.listener.on_disconnected()
    api.disconnect()
    assert not api.active
    # Once disconnected it should not try to reconnect (should not raise the ConnectionRefusedError).
    api.listener.on_disconnected()


def test_expected_error_raised_on_subscription_failure():
    with patch('iotics.host.api.search_api.StompWSConnection12', autospec=True):
        with patch('iotics.host.api.search_api.SearchStompListener') as mock_listener:
            error_msg = 'Dummy error'
            mock_listener.return_value.errors = {SearchAPI.sub_topic: error_msg}
            expected_error_msg = f'Error subscribing to {SearchAPI.sub_topic}: {error_msg}'
            with pytest.raises(DataSourcesStompError, match=expected_error_msg):
                QApiFactory(ConfTest(), AgentAuthTest()).get_search_api()


def test_missing_diconnect_handler_should_not_raise_errors():
    listener = SearchStompListener(None)
    listener.on_disconnected()


def test_error_deserialization_error():
    listener = SearchStompListener(None)
    tx_ref = 'dummy'
    listener.on_error(headers={TXREF_HEADER: f'{tx_ref}_page'}, body='')
    assert listener.errors[tx_ref] == ['Deserialization error: Expecting value: line 1 column 1 (char 0)']


def test_message_deserialization_error():
    listener = SearchStompListener(None)
    tx_ref = 'dummy'
    listener.on_message(headers={TXREF_HEADER: f'{tx_ref}_page0'}, body='')
    assert listener.errors[tx_ref] == ['Deserialization error: Response does not have twins list']


@patch('iotics.host.api.search_api.PAGE_LENGTH', 2)
def test_listener_message_pagination():
    listener = SearchStompListener(None)
    tx_ref = 'dummy'
    response = json.dumps({'twins': [
        {'id': {'value': 'twin1'}},
        {'id': {'value': 'twin2'}},
    ]})
    search_function = MagicMock()
    last_page = 0
    listener.searches[tx_ref] = search_function, last_page

    listener.on_message(headers={TXREF_HEADER: f'{tx_ref}_page0'}, body=response)
    search_function, current_last_page = listener.searches[tx_ref]
    assert current_last_page == 1
    search_function.assert_called_once_with(page=current_last_page)


def test_error_subscription_error():
    """test TXREF_HEADER not containing a _page which it wont for
    the subscription shared across all searches
    """
    listener = SearchStompListener(None)
    tx_ref = 'txref-DH2CjRmzDf'
    listener.on_error(headers={TXREF_HEADER: f'{tx_ref}'}, body='')
    assert listener.errors[tx_ref] == ['Deserialization error: Expecting value: line 1 column 1 (char 0)']


@pytest.mark.parametrize('page', ('', '_page', '_pageNotAnInteger'))
def test_message_invalid_page_number(caplog, page):
    listener = SearchStompListener(None)
    tx_ref = 'dummy'

    with caplog.at_level(logging.ERROR):
        listener.on_message(headers={TXREF_HEADER: f'{tx_ref}{page}'}, body='')
        assert 'Received a message without an integer page number' in caplog.text
