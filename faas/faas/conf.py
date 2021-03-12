from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf

ENV_VAR_PREFIX = 'FAAS_'


class FaaSConf(DataSourcesConfBase):
    """FaaS configuration."""
    auth: AuthConf

    @staticmethod
    def get_conf(file_path: str = None) -> 'FaaSConf':
        return get_conf(FaaSConf, ENV_VAR_PREFIX, file_path, nested_env_conf_separator='__')
