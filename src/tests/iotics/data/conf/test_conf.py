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
from os.path import join

import pytest
import yaml
from pydantic import ValidationError

from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf
from iotics.host.exceptions import DataSourcesConfigurationError
from tests.iotics.data.conf.helper_test import set_env

ENV_VAR_PREFIX = 'AMAZING_CONNECTOR_'


@pytest.fixture
def file_conf_data():
    return {
        'qapi_url': 'http://localhost:8080',
        'root_log_level': 'DEBUG',
        'auth': {'user_seed': 'a user seed',
                 'user_key_name': 'a user key name',
                 'user_name': 'a user name',
                 'agent_seed': 'an agent seed',
                 'agent_key_name': 'an agent key name',
                 'agent_name': 'an agent name',
                 'resolver_host': 'http://plop'},
        'ext_url': 'https://ext_api',
        'a_float_value': '12.3',
    }


@pytest.fixture
def conf_yaml_file(work_dir, file_conf_data):
    conf_file_path = join(work_dir, 'conf.yaml')
    with open(conf_file_path, 'w') as file_descr:
        yaml.dump(file_conf_data, file_descr)
    return conf_file_path


class AmazingConnectorConf(DataSourcesConfBase):
    auth: AuthConf
    ext_url: str
    a_float_value: float


def test_should_load_conf_data_from_environment():
    env_conf_data = {
        # variables can be lower case
        f'{ENV_VAR_PREFIX}qapi_url': 'http://localhost:8080',
        f'{ENV_VAR_PREFIX}ROOT_LOG_LEVEL': 'DEBUG',
        f'{ENV_VAR_PREFIX}AUTH__USER_SEED': 'a user seed',
        f'{ENV_VAR_PREFIX}AUTH__USER_KEY_NAME': 'a user key name',
        f'{ENV_VAR_PREFIX}AUTH__USER_NAME': 'a user name',
        f'{ENV_VAR_PREFIX}AUTH__AGENT_SEED': 'an agent seed',
        f'{ENV_VAR_PREFIX}AUTH__AGENT_KEY_NAME': 'an agent key name',
        f'{ENV_VAR_PREFIX}AUTH__AGENT_NAME': 'an agent name',
        f'{ENV_VAR_PREFIX}AUTH__RESOLVER_HOST': 'http://plop',
        f'{ENV_VAR_PREFIX}EXT_url': 'https://ext_api',
        f'{ENV_VAR_PREFIX}A_FLOAT_VALUE': '12.3',
    }
    with set_env(env_conf_data):
        conf = get_conf(AmazingConnectorConf, ENV_VAR_PREFIX)
    assert conf.qapi_url == env_conf_data[f'{ENV_VAR_PREFIX}qapi_url']
    assert conf.root_log_level == env_conf_data[f'{ENV_VAR_PREFIX}ROOT_LOG_LEVEL']
    assert conf.ext_url == env_conf_data[f'{ENV_VAR_PREFIX}EXT_url']
    assert conf.a_float_value == float(env_conf_data[f'{ENV_VAR_PREFIX}A_FLOAT_VALUE'])
    assert conf.auth.user_seed == env_conf_data[f'{ENV_VAR_PREFIX}AUTH__USER_SEED']
    assert conf.auth.user_key_name == env_conf_data[f'{ENV_VAR_PREFIX}AUTH__USER_KEY_NAME']
    assert conf.auth.user_name == env_conf_data[f'{ENV_VAR_PREFIX}AUTH__USER_NAME']
    assert conf.auth.agent_seed == env_conf_data[f'{ENV_VAR_PREFIX}AUTH__AGENT_SEED']
    assert conf.auth.agent_key_name == env_conf_data[f'{ENV_VAR_PREFIX}AUTH__AGENT_KEY_NAME']
    assert conf.auth.agent_name == env_conf_data[f'{ENV_VAR_PREFIX}AUTH__AGENT_NAME']


def test_should_load_conf_data_from_yaml_file(file_conf_data, conf_yaml_file):
    conf = get_conf(AmazingConnectorConf, ENV_VAR_PREFIX, file_path=conf_yaml_file)
    assert conf.qapi_url == file_conf_data['qapi_url']
    assert conf.root_log_level == file_conf_data['root_log_level']
    assert conf.ext_url == file_conf_data['ext_url']
    assert conf.a_float_value == float(file_conf_data['a_float_value'])
    assert conf.auth.user_seed == file_conf_data['auth']['user_seed']
    assert conf.auth.user_key_name == file_conf_data['auth']['user_key_name']
    assert conf.auth.user_name == file_conf_data['auth']['user_name']
    assert conf.auth.agent_seed == file_conf_data['auth']['agent_seed']
    assert conf.auth.agent_key_name == file_conf_data['auth']['agent_key_name']
    assert conf.auth.agent_name == file_conf_data['auth']['agent_name']


def test_get_conf_file_should_be_overwritten_with_env(work_dir, conf_yaml_file, file_conf_data):
    env_conf_data = {
        f'{ENV_VAR_PREFIX}QAPI_URL': 'http://demo:9090',
        f'{ENV_VAR_PREFIX}AUTH__USER_SEED': 'an other seed',
    }
    assert file_conf_data['qapi_url'] != env_conf_data[f'{ENV_VAR_PREFIX}QAPI_URL'], 'test configuration error'
    assert file_conf_data['auth']['user_seed'] !=\
        env_conf_data[f'{ENV_VAR_PREFIX}AUTH__USER_SEED'], 'test configuration error'

    with set_env(env_conf_data):
        conf = get_conf(AmazingConnectorConf, ENV_VAR_PREFIX, file_path=conf_yaml_file)
    assert conf.qapi_url == env_conf_data[f'{ENV_VAR_PREFIX}QAPI_URL']
    assert conf.auth.user_seed == env_conf_data[f'{ENV_VAR_PREFIX}AUTH__USER_SEED']


def test_get_conf_should_raise_an_error_if_not_a_file(work_dir):
    conf_file_path = join(work_dir, 'plop.yaml')
    with pytest.raises(DataSourcesConfigurationError) as err_wrapper:
        get_conf(AmazingConnectorConf, ENV_VAR_PREFIX, file_path=conf_file_path)
    assert isinstance(err_wrapper.value.__cause__, IOError)


def test_get_conf_should_raise_an_error_if_invalid_yaml(work_dir):
    conf_file_path = join(work_dir, 'plop.yaml')
    with open(conf_file_path, 'wb') as file_descr:
        file_descr.write(b'@@@e&&$')
    with pytest.raises(DataSourcesConfigurationError) as err_wrapper:
        get_conf(AmazingConnectorConf, ENV_VAR_PREFIX, file_path=conf_file_path)
    assert isinstance(err_wrapper.value.__cause__, yaml.YAMLError)


def test_get_conf_should_raise_an_error_if_invalid_conf_from_file(work_dir, file_conf_data):
    conf_file_path = join(work_dir, 'server.yaml')
    file_conf_data['a_float_value'] = 'not a float'
    with open(conf_file_path, 'w') as file_descr:
        yaml.dump(file_conf_data, file_descr)
    with pytest.raises(DataSourcesConfigurationError) as err_wrapper:
        get_conf(AmazingConnectorConf, ENV_VAR_PREFIX, file_path=conf_file_path)
    assert isinstance(err_wrapper.value.__cause__, ValidationError)


def test_get_conf_should_raise_an_error_if_invalid_conf_from_env(work_dir):
    env_conf_data = {
        f'{ENV_VAR_PREFIX}AUTH__USER_SEED': 'a user eed',
        f'{ENV_VAR_PREFIX}AUTH__USER_KEY_NAME': 'a user key name',
        f'{ENV_VAR_PREFIX}A_FLOAT_VALUE': 'not an float',
    }
    with set_env(env_conf_data), pytest.raises(DataSourcesConfigurationError) as err_wrapper:
        get_conf(AmazingConnectorConf, ENV_VAR_PREFIX)
    assert isinstance(err_wrapper.value.__cause__, ValidationError)


def test_get_conf_should_raise_an_error_if_missing_mandatory_field(work_dir):
    env_conf_data = {
        f'{ENV_VAR_PREFIX}AUTH__USER_SEED': 'a user seed',
        f'{ENV_VAR_PREFIX}A_FLOAT_VALUE': 'not an float',
    }
    with set_env(env_conf_data), pytest.raises(DataSourcesConfigurationError) as err_wrapper:
        get_conf(AmazingConnectorConf, ENV_VAR_PREFIX)
    assert isinstance(err_wrapper.value.__cause__, ValidationError)
