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
from iotics.host.exceptions import DataSourcesConfigurationError
from {{cookiecutter.module_name}}.conf import {{cookiecutter.publisher_class_name}}Conf


@pytest.fixture
def min_conf_data():
    # TODO: update with publisher specific mandatory conf
    return {
        'auth': {
            'user_seed': 'a user seed', 'agent_seed': 'an agent seed',
            'resolver_host': 'http:plop:5000'
        }
    }


@pytest.fixture
def full_conf_data(min_conf_data):
    # TODO: update with publisher specific mandatory conf and overridden default values

    return {
        'qapi_url': 'http://plop:8080',
        'root_log_level': 'DEBUG',
        'auth': min_conf_data['auth'],
    }


def write_yaml_conf_file(work_dir, conf_data):
    conf_file_path = join(work_dir, 'conf.yaml')
    with open(conf_file_path, 'w') as file_descr:
        yaml.dump(conf_data, file_descr)
    return conf_file_path


def test_should_load_minimal_conf_with_default_values(work_dir, min_conf_data):
    conf_file_path = write_yaml_conf_file(work_dir, min_conf_data)
    conf = {{cookiecutter.publisher_class_name}}Conf.get_conf(conf_file_path)
    assert conf.auth.user_seed == min_conf_data['auth']['user_seed']
    assert conf.auth.agent_seed == min_conf_data['auth']['agent_seed']
    assert conf.auth.resolver_host == min_conf_data['auth']['resolver_host']
    assert conf.qapi_url == 'http://localhost:8081/qapi'
    assert conf.root_log_level is None
    # TODO: add checks on values for publisher specific conf


def test_should_load_conf_with_full_values(work_dir, full_conf_data):
    conf_file_path = write_yaml_conf_file(work_dir, full_conf_data)
    conf = {{cookiecutter.publisher_class_name}}Conf.get_conf(conf_file_path)
    assert conf.qapi_url == full_conf_data['qapi_url']
    assert conf.auth.user_seed == full_conf_data['auth']['user_seed']
    assert conf.auth.agent_seed == full_conf_data['auth']['agent_seed']
    assert conf.auth.resolver_host == full_conf_data['auth']['resolver_host']
    assert conf.root_log_level == full_conf_data['root_log_level']
    # TODO: add checks on values for publisher specific conf


# TODO: update with all the mandatory values
@pytest.mark.parametrize('missing_conf', ('user_seed', 'agent_seed'))
def test_should_raise_if_missing_mandatory_value_from_base_conf(work_dir, min_conf_data, missing_conf):
    min_conf_data['auth'].pop(missing_conf)
    conf_file_path = write_yaml_conf_file(work_dir, min_conf_data)

    with pytest.raises(DataSourcesConfigurationError) as err_wrapper:
        {{cookiecutter.publisher_class_name}}Conf.get_conf(conf_file_path)
    assert isinstance(err_wrapper.value.__cause__, ValidationError)
