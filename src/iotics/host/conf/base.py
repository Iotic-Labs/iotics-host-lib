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
from typing import Dict, Type

import yaml
from pydantic import BaseModel, ValidationError

from iotics.host.conf.helper import deep_dict_merge, get_data_from_env
from iotics.host.exceptions import DataSourcesConfigurationError


class AuthConf(BaseModel):
    user_seed: str
    user_key_name: str = '00'
    user_name: str = '#user-0'

    agent_seed: str
    agent_key_name: str = '00'
    agent_name: str = '#agent-0'

    resolver_host: str


class DataSourcesConfBase(BaseModel):
    qapi_url: str = 'http://localhost:8081/qapi'
    qapi_stomp_url: str = 'ws://localhost:8080/ws'
    root_log_level: str = None
    verify_ssl: bool = True

    @staticmethod
    def read_conf_file(file_path: str) -> Dict[str, str]:
        try:
            with open(file_path) as f_descr:
                return yaml.load(f_descr, Loader=yaml.FullLoader)
        except IOError as err:
            raise DataSourcesConfigurationError(f'Cannot read file {file_path}: {err}') from err
        except (yaml.YAMLError, TypeError) as err:
            raise DataSourcesConfigurationError(f'Cannot parse Yaml file {file_path}: {err}') from err


def get_conf(conf_class: Type[DataSourcesConfBase], env_var_prefix: str, file_path: str = None,
             nested_env_conf_separator: str = '__'):
    """
        Load configuration in the provided Pydantic models.
        The conf data are overwritten in this order:
        - data loaded from a Yaml file
        - data loaded from the env

        To be detected as configuration data, the configuration variables must start with the provided
        `env_var_prefix`. For nested Pydantic configuration the `nested_env_conf_separator` must be used.
        Example:
            ENV_PREFIX = 'MY_SERVER_'
            class MainConf(BaseModel):
                host: str
                auth: AuthConf

            class AuthConf(BaseModel):
                seed: str
                user: str

            Env variables:
                - MY_SERVER_HOST = 'some value'
                - MY_SERVER_AUTH__USER = 'some value' # `user` in a value from the `auth` nested conf
    """
    data_from_file = conf_class.read_conf_file(file_path) if file_path else {}
    data_from_env = get_data_from_env(env_var_prefix, nested_env_conf_separator)
    conf_data = deep_dict_merge(data_from_file, data_from_env)
    try:
        return conf_class(**conf_data)
    except ValidationError as err:
        raise DataSourcesConfigurationError(f'Invalid ServerConf configuration: {err}\n{conf_data}') from err
