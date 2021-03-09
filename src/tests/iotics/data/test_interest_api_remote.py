import pytest
from iotic.web.rest.client.qapi import ApiException, Configuration, InterestApi as InterestClient

from iotics.host.api.interest_api import get_interest_api, InterestApi
from iotics.host.api.qapi import QApiFactory
from iotics.host.exceptions import DataSourcesQApiError, DataSourcesQApiHttpError
from tests.iotics.data.mocks import AgentAuthTest, ConfTest, FakeApiClient, get_api_exception


def test_should_get_an_interest_api():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_interest_api()
    assert isinstance(api, InterestApi)


def test_should_raise_qapi_error_if_connection_error():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_interest_api()
    with pytest.raises(DataSourcesQApiError) as error:
        api.get_feed_last_stored('host_id', 'follower_twin_id', 'followed_twin_id', 'feed_id')
    assert 'Max retries exceeded with' in str(error.value)


@pytest.mark.parametrize(
    'arguments,missing_param', [
        ([None, 'follower_twin_id', 'followed_twin_id', 'feed_id'], 'host_id'),
        (['host_id', 'follower_twin_id', None, 'feed_id'], 'followed_twin_id'),
        (['host_id', None, 'followed_twin_id', 'feed_id'], 'follower_twin_id'),
        (['host_id', 'follower_twin_id', 'followed_twin_id', None], 'followed_feed_id'),
    ])
def test_should_raise_qapi_error_if_missing_param(arguments, missing_param):
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_interest_api()
    with pytest.raises(DataSourcesQApiError) as error:
        api.get_feed_last_stored(*arguments)
    assert f'Missing the required parameter `{missing_param}`' in str(error.value)


def test_should_raise_qapi_http_error_if_http_error(api_exception):
    api = InterestApi(InterestClient(api_client=FakeApiClient(error=api_exception)), client_app_id='app1')
    with pytest.raises(DataSourcesQApiHttpError) as error:
        api.get_feed_last_stored('host_id', 'follower_twin_id', 'did:iotics:e1', 'feed_id')
    assert '' in str(error.value)


def get_test_interest_api():
    api = get_interest_api(Configuration(host='http://a_host_url'))
    api.rest_api_client.api_client = FakeApiClient(error=get_api_exception())
    return api


def get_last_stored_call():
    return get_test_interest_api().get_feed_last_stored(
        host_id='host_id',
        follower_twin_id='a follower twin id',
        followed_twin_id='a followed twin id',
        feed_id='a feed id'
    )


@pytest.mark.parametrize('client_call', (get_last_stored_call,))
def test_client_validation_is_ok_should_raise_connection_error(client_call, twin_id, feed_id):
    """
    Test the Openapi client side validation. The client side validation occurs before the actual rest call.
    Here we are using a fake client for the rest call. It will raise an HTTP Not found when it will try to request
    the server. If the error is raised, that means the client side validation passed.
    Ideally we could mock the rest call but it is not something out of the box with the generated client (for example
    we can not use `requests_mock`).
    This test ensures the code is inline with the dependency of the iotic.web.rest.client. It will detect a client
    code breaking change.
    """
    with pytest.raises(DataSourcesQApiHttpError) as wrapper:
        client_call()
    assert isinstance(wrapper.value.__cause__, ApiException)
