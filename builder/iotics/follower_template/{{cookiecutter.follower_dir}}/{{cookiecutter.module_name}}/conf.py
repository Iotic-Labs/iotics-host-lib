from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf

ENV_VAR_PREFIX = '{{cookiecutter.conf_env_var_prefix}}'


class {{cookiecutter.follower_class_name}}Conf(DataSourcesConfBase):
    """{{cookiecutter.follower_class_name}} configuration."""
    auth: AuthConf{% if cookiecutter.add_example_code == "YES" %}
    update_frequency_seconds: int = 300{% endif %}

    @staticmethod
    def get_conf(file_path: str = None) -> '{{cookiecutter.follower_class_name}}Conf':
        return get_conf({{cookiecutter.follower_class_name}}Conf, ENV_VAR_PREFIX, file_path, nested_env_conf_separator='__')
