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
import pytest
from iotic.web.rest.client.qapi import ApiException, Configuration, InterestApi as InterestClient

from iotics.host.api.interest_api import get_interest_api, InterestApi
from iotics.host.api.qapi import QApiFactory
from iotics.host.exceptions import DataSourcesQApiError, DataSourcesQApiHttpError
from tests.iotics.data.mocks import AgentAuthTest, ConfTest, FakeApiClient, get_api_exception


def test_should_get_a_interest_api():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_interest_api()
    assert isinstance(api, InterestApi)


def test_should_raise_qapi_error_if_connection_error():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_interest_api()
    with pytest.raises(DataSourcesQApiError):
        api.get_feed_last_stored_local('follower_twin_id', 'followed_twin_id', 'feed_id')


@pytest.mark.parametrize(
    'arguments,missing_param', [
        (['follower_twin_id', None, 'feed_id'], 'followed_twin_id'),
        ([None, 'followed_twin_id', 'feed_id'], 'follower_twin_id'),
        (['follower_twin_id', 'followed_twin_id', None], 'followed_feed_id'),
    ])
def test_should_raise_qapi_error_if_missing_param(arguments, missing_param):
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_interest_api()
    with pytest.raises(DataSourcesQApiError) as error:
        api.get_feed_last_stored_local(*arguments)
    assert f'Missing the required parameter `{missing_param}`' in str(error.value)


def test_should_raise_qapi_http_error_if_http_error(api_exception):
    api = InterestApi(InterestClient(api_client=FakeApiClient(error=api_exception)), client_app_id='app1')
    with pytest.raises(DataSourcesQApiHttpError):
        api.get_feed_last_stored_local('follower_twin_id', 'did:iotics:e1', 'feed_id')


def get_test_interest_api():
    api = get_interest_api(Configuration(host='http://a_host_url'))
    api.rest_api_client.api_client = FakeApiClient(error=get_api_exception())
    return api


def get_last_stored_local_call():
    return get_test_interest_api().get_feed_last_stored_local(
        follower_twin_id='a follower twin id',
        followed_twin_id='a followed twin id',
        feed_id='a feed id'
    )


@pytest.mark.parametrize('client_call', (get_last_stored_local_call,))
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
