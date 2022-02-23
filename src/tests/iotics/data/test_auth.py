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
import pytest

from iotics.host.auth import AgentAuthBuilder
from iotics.host.exceptions import DataSourcesAuthException

AGENT_ID = 'did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM'


@pytest.fixture
def valid_auth_params():
    return dict(resolver_url='http://locahost',
                user_seed='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                user_key_name='00',
                agent_seed='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                agent_key_name='00')


def test_auth_builder_should_raise_if_invalid_seed(valid_auth_params):
    valid_auth_params['agent_seed'] = ' invalid seed'
    with pytest.raises(DataSourcesAuthException)as exc_wrapper:
        AgentAuthBuilder.build_agent_auth(**valid_auth_params)
    assert 'Seeds must be hex string 32-64 chars' in str(exc_wrapper.value)


def test_auth_builder_should_raise_if_resolver_not_found(valid_auth_params):
    with pytest.raises(DataSourcesAuthException) as exc_wrapper:
        AgentAuthBuilder.build_agent_auth(**valid_auth_params)
    assert 'Failed to retrieve token from' in str(exc_wrapper.value)
