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
from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf

ENV_VAR_PREFIX = '{{cookiecutter.conf_env_var_prefix}}'


class {{cookiecutter.publisher_class_name}}Conf(DataSourcesConfBase):
    """{{cookiecutter.publisher_class_name}} configuration."""
    auth: AuthConf{% if cookiecutter.add_example_code == "YES" %}
    update_frequency_seconds: int = 10{% endif %}

    @staticmethod
    def get_conf(file_path: str = None) -> '{{cookiecutter.publisher_class_name}}Conf':
        return get_conf(
            {{cookiecutter.publisher_class_name}}Conf,
            ENV_VAR_PREFIX,
            file_path,
            nested_env_conf_separator='__'
        )
