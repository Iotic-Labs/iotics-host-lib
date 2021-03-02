from http import HTTPStatus

import pytest

from iotics.host.auth import AgentAuthBuilder
from iotics.host.exceptions import DataSourcesAuthException

AGENT_ID = 'did:iotics:iotNBCuchizDWag9LUYaZCRMFBTKHUn9uakr'


@pytest.fixture
def valid_auth_params():
    return dict(host='http://locahost',
                seed='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                user_id='did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM',
                password=b'plop')


def test_auth_builder_should_raise_if_invalid_seed(valid_auth_params):
    valid_auth_params['seed'] = ' invalid seed'
    with pytest.raises(DataSourcesAuthException)as exc_wrapper:
        AgentAuthBuilder.build_agent_auth(**valid_auth_params)
    assert 'Seed must be hex string 32-64 chars' in str(exc_wrapper.value)


def test_auth_builder_should_raise_if_invalid_user_id(valid_auth_params):
    valid_auth_params['user_id'] = ' invalid user_id'
    with pytest.raises(DataSourcesAuthException) as exc_wrapper:
        AgentAuthBuilder.build_agent_auth(**valid_auth_params)
    assert 'Identifier does not match pattern ^did:iotics:iot' in str(exc_wrapper.value)


def test_auth_builder_should_raise_if_resolver_not_found(valid_auth_params):
    with pytest.raises(DataSourcesAuthException) as exc_wrapper:
        AgentAuthBuilder.build_agent_auth(**valid_auth_params)
    assert 'Failed to establish a new connection' in str(exc_wrapper.value)


def test_auth_builder_should_raise_if_no_agent_doc(requests_mock, valid_auth_params):
    requests_mock.get(f'http://locahost/1.0/discover/{AGENT_ID}',
                      status_code=HTTPStatus.NOT_FOUND)
    with pytest.raises(DataSourcesAuthException) as exc_wrapper:
        AgentAuthBuilder.build_agent_auth(**valid_auth_params)
    assert f'Agent ID {AGENT_ID} does not exist' in str(exc_wrapper.value)
