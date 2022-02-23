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
import re
import sys
import logging

"""
Update-context hack: https://github.com/samj1912/cookiecutter-advanced-demo

By putting Jinja in this docstring, we are able to update the context before project generation, allowing us to
use the space for defaults in the variable prompts to provide user help, and then replace them with the actual
defaults here. Support for actual variable help strings in cookiecutter is planned here:
https://github.com/cookiecutter/cookiecutter/issues/794#issuecomment-455642359

{% if cookiecutter.project_name == "A project name used in the doc (ex: Random Temperature Generator)" %}
{{ cookiecutter.update({"project_name": "Random Temperature Generator" }) }}
{% endif %}
{% if cookiecutter.publisher_dir == "publisher directory name (ex: random-temp-pub)" %}
{{ cookiecutter.update({"publisher_dir": "random-temp-pub" }) }}
{% endif %}
{% if cookiecutter.module_name == "python module name (ex: randpub)" %}
{{ cookiecutter.update({"module_name": "randpub" }) }}
{% endif %}
{% if cookiecutter.command_name == "command line name (ex: run-rand-pub)" %}
{{ cookiecutter.update({"command_name": "run-rand-pub" }) }}
{% endif %}
{% if cookiecutter.conf_env_var_prefix == "conf environment variable prefix (ex: RANDPUB_)" %}
{{ cookiecutter.update({"conf_env_var_prefix": "RANDPUB_" }) }}
{% endif %}
{% if cookiecutter.publisher_class_name == "publisher class name (ex: RandomTempPublisher)" %}
{{ cookiecutter.update({"publisher_class_name": "RandomTempPublisher" }) }}
{% endif %}
"""

def validate(value:str, regex:str, err_message:str):
    if not re.match(regex, value):
        logging.error('"%s" is not a valid %s! Regex: %s', value, err_message, regex)
        # exits with status 1 to indicate failure
        sys.exit(1)


MODULE_REGEX = r'^[a-zA-Z][\_a-zA-Z0-9]+$'
validate('{{ cookiecutter.module_name }}', MODULE_REGEX, 'Python module name')

PUBLISHER_DIR_REGEX = r'^[a-zA-Z][\-\_a-zA-Z0-9]+$'
validate('{{ cookiecutter.publisher_dir }}', PUBLISHER_DIR_REGEX, 'publisher directory name')

COMMAND_REGEX = r'^[\.\-\_a-zA-Z0-9]+$'
validate('{{ cookiecutter.command_name }}', COMMAND_REGEX, 'command line name')

ENV_PREFIX_REGEX = r'^[\_A-Z0-9]+\_$'
validate('{{ cookiecutter.conf_env_var_prefix }}', ENV_PREFIX_REGEX, 'configuration environment variable prefix')

CLASS_REGEX = r'^[A-Z][a-zA-Z]+$'
validate('{{ cookiecutter.publisher_class_name }}', CLASS_REGEX, 'Python class name')
