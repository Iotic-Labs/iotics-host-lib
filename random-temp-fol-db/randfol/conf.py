from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf

ENV_VAR_PREFIX = 'RANDFOL_'


class RandomTempFollowerConf(DataSourcesConfBase):
    """RandomTempFollower configuration."""
    auth: AuthConf
    update_frequency_seconds: int = 300

    @staticmethod
    def get_conf(file_path: str = None) -> 'RandomTempFollowerConf':
        return get_conf(RandomTempFollowerConf, ENV_VAR_PREFIX, file_path, nested_env_conf_separator='__')
