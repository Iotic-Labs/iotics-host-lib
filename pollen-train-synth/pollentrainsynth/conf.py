from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf

ENV_VAR_PREFIX_P = 'POLLENTRAINSYNTHP_'
ENV_VAR_PREFIX_F = 'POLLENTRAINSYNTHF_'


class PollenTrainSynthesiserConf(DataSourcesConfBase):
    """PollenTrainSynthesiser configuration."""
    auth: AuthConf
    update_frequency_seconds: int = 300

    @staticmethod
    def get_conf_f(file_path: str = None) -> 'PollenTrainSynthesiserConf':
        return get_conf(PollenTrainSynthesiserConf, ENV_VAR_PREFIX_F, file_path, nested_env_conf_separator='__')

    @staticmethod
    def get_conf_p(file_path: str = None) -> 'PollenTrainSynthesiserConf':
        return get_conf(PollenTrainSynthesiserConf, ENV_VAR_PREFIX_P, file_path, nested_env_conf_separator='__')
