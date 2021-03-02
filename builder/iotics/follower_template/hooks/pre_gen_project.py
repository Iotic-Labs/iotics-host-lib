import re
import sys
import logging

"""
Update-context hack: https://github.com/samj1912/cookiecutter-advanced-demo

By putting Jinja in this docstring, we are able to update the context before project generation, allowing us to
use the space for defaults in the variable prompts to provide user help, and then replace them with the actual
defaults here. Support for actual variable help strings in cookiecutter is planned here:
https://github.com/cookiecutter/cookiecutter/issues/794#issuecomment-455642359

{% if cookiecutter.project_name == "A project name used in the doc (ex: Random Letter Generator)" %}
{{ cookiecutter.update({"project_name": "Random Letter Generator" }) }}
{% endif %}
{% if cookiecutter.follower_dir == "follower directory name (ex: random-let-fol)" %}
{{ cookiecutter.update({"follower_dir": "random-let-fol" }) }}
{% endif %}
{% if cookiecutter.module_name == "python module name (ex: randfol)" %}
{{ cookiecutter.update({"module_name": "randfol" }) }}
{% endif %}
{% if cookiecutter.command_name == "command line name (ex: run-rand-fol)" %}
{{ cookiecutter.update({"command_name": "run-rand-fol" }) }}
{% endif %}
{% if cookiecutter.conf_env_var_prefix == "conf environment variable prefix (ex: RANDFOL_)" %}
{{ cookiecutter.update({"conf_env_var_prefix": "RANDFOL_" }) }}
{% endif %}
{% if cookiecutter.follower_class_name == "follower class name (ex: RandomLetFollower)" %}
{{ cookiecutter.update({"follower_class_name": "RandomLetFollower" }) }}
{% endif %}
"""

def validate(value:str, regex:str, err_message:str):
    if not re.match(regex, value):
        logging.error('"%s" is not a valid %s! Regex: %s', value, err_message, regex)
        # exits with status 1 to indicate failure
        sys.exit(1)


MODULE_REGEX = r'^[a-zA-Z][\_a-zA-Z0-9]+$'
validate('{{ cookiecutter.module_name }}', MODULE_REGEX, 'Python module name')

FOLLOWER_DIR_REGEX = r'^[a-zA-Z][\-\_a-zA-Z0-9]+$'
validate('{{ cookiecutter.follower_dir }}', FOLLOWER_DIR_REGEX, 'follower directory name')

COMMAND_REGEX = r'^[\.\-\_a-zA-Z0-9]+$'
validate('{{ cookiecutter.command_name }}', COMMAND_REGEX, 'command line name')

ENV_PREFIX_REGEX = r'^[\_A-Z0-9]+\_$'
validate('{{ cookiecutter.conf_env_var_prefix }}', ENV_PREFIX_REGEX, 'configuration environment variable prefix')

CLASS_REGEX = r'^[A-Z][a-zA-Z]+$'
validate('{{ cookiecutter.follower_class_name }}', CLASS_REGEX, 'Python class name')
