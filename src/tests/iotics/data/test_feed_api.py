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
import base64
from datetime import datetime, timezone
from functools import partial

import pytest
from iotic.web.rest.client.qapi import ApiException, ApiValueError, Configuration, FeedApi as FeedClient, LangLiteral, \
    Value, ModelProperty, Literal

from iotics.host.api.feed_api import FeedApi, get_feed_api
from iotics.host.api.qapi import QApiFactory
from iotics.host.exceptions import DataSourcesQApiError, DataSourcesQApiHttpError
from tests.iotics.data.mocks import AgentAuthTest, ConfTest, FakeApiClient, get_api_exception


def test_should_get_a_feed_api():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_feed_api()
    assert isinstance(api, FeedApi)


def test_should_raise_qapi_error_if_connection_error():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_feed_api()
    with pytest.raises(DataSourcesQApiError):
        api.list_feeds('did:iotics:e1')


def test_should_raise_qapi_error_if_invalid_data():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_feed_api()
    with pytest.raises(DataSourcesQApiError):
        api.share_feed_data('did:iotics:e1', 'feed_name',
                            data='bad_encoding{}')


def test_should_raise_qapi_http_error_if_http_error(api_exception):
    api = FeedApi(
        FeedClient(api_client=FakeApiClient(error=api_exception)), client_app_id='app1'
    )
    with pytest.raises(DataSourcesQApiHttpError):
        api.list_feeds('did:iotics:e1')


def get_test_feed_api():
    api = get_feed_api(Configuration(host='http://a_host_url'))
    api.rest_api_client.api_client = FakeApiClient(error=get_api_exception())
    return api


@pytest.mark.parametrize('client_call', (partial(get_test_feed_api().create_feed, feed_id='a feed id'),
                                         get_test_feed_api().list_feeds,
                                         partial(get_test_feed_api().delete_feed, feed_id='a feed id'),
                                         partial(get_test_feed_api().describe_feed, feed_id='a feed id'),
                                         partial(get_test_feed_api().describe_remote_feed, feed_id='a feed id', remote_host_id='a remote host id'),  # noqa: E501 pylint: disable=C0301
                                         partial(get_test_feed_api().update_feed, feed_id='a feed id'),
                                         partial(get_test_feed_api().share_feed_data, feed_id='a feed id'),
                                         ))
def test_should_raise_if_client_check_fails(client_call):
    with pytest.raises(DataSourcesQApiError) as wrapper:
        client_call(twin_id=None)
    assert isinstance(wrapper.value.__cause__, ApiValueError)
    assert 'Missing the required parameter `twin_id`' in str(wrapper.value)


def get_create_feed_call():
    return partial(get_test_feed_api().create_feed, twin_id='a twin id', feed_id='a feed id')


def get_delete_feed_call():
    return partial(get_test_feed_api().delete_feed, twin_id='a twin id', feed_id='a feed id')


def get_describe_feed_call():
    return partial(get_test_feed_api().describe_feed, twin_id='a twin id', feed_id='a feed id')


def get_describe_remote_feed_call():
    return partial(
        get_test_feed_api().describe_remote_feed, twin_id='a twin id',
        feed_id='a feed id', remote_host_id='a remote id'
    )


def get_list_feeds_call():
    return partial(get_test_feed_api().list_feeds, twin_id='a twin id')


def get_update_feed_call():
    return partial(get_test_feed_api().update_feed, twin_id='a twin id', feed_id='a feed id',
                   add_props=(ModelProperty(key='key1', lang_literal_value=LangLiteral(lang='fr', value='une valeur')),
                              ModelProperty(key='key2', literal_value=Literal(data_type='data type', value='a value'))),
                   add_values=(Value(comment='a comment', data_type='a data type', label='a label', unit='a unit'),),
                   del_values=('a value',),
                   store_last=True,
                   )


def get_share_data_call():
    return partial(get_test_feed_api().share_feed_data, twin_id='a twin id', feed_id='a feed id',
                   data=base64.b64encode('some data'.encode('utf8')).decode(),
                   mime='app/text',
                   occurred_at=datetime.now(timezone.utc)
                   )


@pytest.mark.parametrize('client_call', (get_create_feed_call(),
                                         get_list_feeds_call(),
                                         get_delete_feed_call(),
                                         get_describe_feed_call(),
                                         get_describe_remote_feed_call(),
                                         get_update_feed_call(),
                                         get_share_data_call(),
                                         ))
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
