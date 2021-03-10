from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf

ENV_VAR_PREFIX = 'METLOC1_'


class MetofficeLocationOneConf(DataSourcesConfBase):
    """MetofficeLocationOne configuration."""
    auth: AuthConf
    update_frequency_seconds: int = 600

    @staticmethod
    def get_conf(file_path: str = None) -> 'MetofficeLocationOneConf':
        return get_conf(
            MetofficeLocationOneConf,
            ENV_VAR_PREFIX,
            file_path,
            nested_env_conf_separator='__'
        )
