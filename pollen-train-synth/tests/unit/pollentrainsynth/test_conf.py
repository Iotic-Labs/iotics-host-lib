from os.path import join

import pytest
import yaml
from pydantic import ValidationError
from iotics.host.exceptions import DataSourcesConfigurationError
from pollentrainsynth.conf import PollenTrainSynthesiserConf


@pytest.fixture
def min_conf_data():
    # TODO: update with follower specific mandatory conf
    return {
        'auth': {'seed': 'a seed', 'user': 'did:iotics:USERKEY', 'resolver_host': 'http:plop:5000'}
    }


@pytest.fixture
def full_conf_data(min_conf_data):
    # TODO: update with follower specific mandatory conf and overridden default values

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
    conf = PollenTrainSynthesiserConf.get_conf(conf_file_path)
    assert conf.auth.seed == min_conf_data['auth']['seed']
    assert conf.auth.user == min_conf_data['auth']['user']
    assert conf.auth.resolver_host == min_conf_data['auth']['resolver_host']
    assert conf.qapi_url == 'http://localhost:8081/qapi'
    assert conf.root_log_level is None
    # TODO: add checks on values for follower specific conf


def test_should_load_conf_with_full_values(work_dir, full_conf_data):
    conf_file_path = write_yaml_conf_file(work_dir, full_conf_data)
    conf = PollenTrainSynthesiserConf.get_conf(conf_file_path)
    assert conf.qapi_url == full_conf_data['qapi_url']
    assert conf.auth.seed == full_conf_data['auth']['seed']
    assert conf.auth.user == full_conf_data['auth']['user']
    assert conf.auth.resolver_host == full_conf_data['auth']['resolver_host']
    assert conf.root_log_level == full_conf_data['root_log_level']
    # TODO: add checks on values for follower specific conf


# TODO: update with all the mandatory values
@pytest.mark.parametrize('missing_conf', ('seed', 'user'))
def test_should_raise_if_missing_mandatory_value_from_base_conf(work_dir, min_conf_data, missing_conf):
    min_conf_data['auth'].pop(missing_conf)
    conf_file_path = write_yaml_conf_file(work_dir, min_conf_data)

    with pytest.raises(DataSourcesConfigurationError) as err_wrapper:
        PollenTrainSynthesiserConf.get_conf(conf_file_path)
    assert isinstance(err_wrapper.value.__cause__, ValidationError)
