from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf

ENV_VAR_PREFIX = 'WEATHERTEMPL_'


class WeatherTemplateConf(DataSourcesConfBase):
    """WeatherTemplate configuration."""
    auth: AuthConf
    update_frequency_seconds: int = 300

    @staticmethod
    def get_conf(file_path: str = None) -> 'WeatherTemplateConf':
        return get_conf(WeatherTemplateConf, ENV_VAR_PREFIX, file_path, nested_env_conf_separator='__')
