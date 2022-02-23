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
from functools import partial

import pytest
from iotic.web.rest.client.qapi import ApiException, ApiValueError, Configuration, GeoLocation, GeoLocationUpdate, \
    LangLiteral, Literal, ModelProperty, StringLiteral, TwinApi as TwinClient, UpsertFeedWithMeta, Uri, Value, \
    Visibility
from iotics.host.api.qapi import QApiFactory
from iotics.host.api.twin_api import get_twin_api, TwinApi
from iotics.host.exceptions import DataSourcesQApiError, DataSourcesQApiHttpError

from tests.iotics.data.mocks import AgentAuthTest, ConfTest, FakeApiClient, get_api_exception


def test_should_get_an_twin_api():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_twin_api()
    assert isinstance(api, TwinApi)


def test_should_raise_qapi_error_if_connection_error():
    api = QApiFactory(ConfTest(), AgentAuthTest()).get_twin_api()
    with pytest.raises(DataSourcesQApiError):
        api.list_twins()


def test_should_raise_qapi_http_error_if_http_error(api_exception):
    api = TwinApi(TwinClient(api_client=FakeApiClient(error=api_exception)), 'app1')
    with pytest.raises(DataSourcesQApiHttpError):
        api.list_twins()


def get_test_twin_api():
    api = get_twin_api(Configuration(host='http://a_host_url'))
    api.rest_api_client.api_client = FakeApiClient(error=get_api_exception())
    return api


@pytest.mark.parametrize('client_call', (get_test_twin_api().delete_twin,
                                         get_test_twin_api().describe_twin,
                                         partial(get_test_twin_api().describe_remote_twin,
                                                 remote_host_id='a remote host id'),  # noqa: E501 pylint: disable=C0301
                                         partial(get_test_twin_api().update_twin, ),
                                         ))
def test_should_raise_if_client_check_fails(client_call):
    with pytest.raises(DataSourcesQApiError) as wrapper:
        client_call(twin_id=None)
    assert isinstance(wrapper.value.__cause__, ApiValueError)
    assert 'Missing the required parameter `twin_id`' in str(wrapper.value)


def get_create_twin_call():
    return partial(get_test_twin_api().create_twin, twin_id='a twin id')


def get_delete_twin_call():
    return partial(get_test_twin_api().delete_twin, twin_id='a twin id')


def get_describe_twin_call():
    return partial(get_test_twin_api().describe_twin, twin_id='a twin id')


def get_describe_remote_twin_call():
    return partial(
        get_test_twin_api().describe_remote_twin, twin_id='a twin id',
        remote_host_id='a remote host id'
    )


def get_list_twins_call():
    return partial(get_test_twin_api().list_twins)


def get_update_twin_call():
    return partial(get_test_twin_api().update_twin, twin_id='a twin id',
                   new_visibility=Visibility.PUBLIC,
                   location=GeoLocationUpdate(location=GeoLocation(lat=0.3455, lon=1.234)),
                   add_props=(ModelProperty(key='key1', lang_literal_value=LangLiteral(lang='fr', value='une valeur')),
                              ModelProperty(key='key2', literal_value=Literal(data_type='data type', value='a value'))),
                   del_props=(ModelProperty(key='key3', string_literal_value=StringLiteral(value='a value')),
                              ModelProperty(key='key4', uri_value=Uri(value='a value'))),
                   del_props_by_key=('key6', 'key7'),
                   clear_all_props=True)


def get_upsert_twin_call():
    props = (ModelProperty(key='key1', lang_literal_value=LangLiteral(lang='fr', value='une valeur')),
             ModelProperty(key='key2', literal_value=Literal(data_type='data type', value='a value')))
    return partial(get_test_twin_api().upsert_twin, twin_id='a twin id',
                   visibility=Visibility.PUBLIC,
                   location=GeoLocation(lat=0.3455, lon=1.234),
                   properties=props,
                   feeds=(UpsertFeedWithMeta(
                       id='a feed',
                       properties=props,
                       store_last=True,
                       values=(Value(comment='a comment', data_type='a data type', label='a label', unit='a unit'),)
                   )))


@pytest.mark.parametrize('client_call', (get_create_twin_call(),
                                         get_list_twins_call(),
                                         get_delete_twin_call(),
                                         get_describe_twin_call(),
                                         get_describe_remote_twin_call(),
                                         get_update_twin_call(),
                                         get_upsert_twin_call(),
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
