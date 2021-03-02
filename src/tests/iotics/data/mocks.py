from http import HTTPStatus
from unittest.mock import MagicMock

from iotic.web.rest.client.qapi import ApiClient, ApiException

from iotics.host.conf.base import DataSourcesConfBase


class AgentAuthTest:
    # pylint: disable=R0201
    def __init__(self):
        self.make_agent_auth_token = MagicMock(return_value='a_token')


class ConfTest(DataSourcesConfBase):
    pass


class FakeApiClient(ApiClient):
    def __init__(self, error: Exception = None):
        super().__init__()
        self.error = error

    def request(self, method, url, query_params=None, headers=None,
                post_params=None, body=None, _preload_content=True,
                _request_timeout=None):
        raise self.error


class MockStompConnection(MagicMock):
    def set_listener(self, name, listener):
        self.listener = listener  # pylint: disable=attribute-defined-outside-init

    def subscribe(self, destination, headers=None, **kwargs):
        try:
            headers['receipt-id'] = headers.pop('receipt')
        except KeyError:
            pass
        self.listener.on_receipt(headers, 'foo')


def get_api_exception():
    ex = ApiException(status=HTTPStatus.NOT_FOUND)
    ex.body = b'an error'
    return ex
