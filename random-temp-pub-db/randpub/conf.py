from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf

ENV_VAR_PREFIX = "RANDPUB_"


class RandomTempPublisherConf(DataSourcesConfBase):
    """RandomTempPublisher configuration."""

    auth: AuthConf
    update_frequency_seconds: int = 5

    @staticmethod
    def get_conf(file_path: str = None) -> "RandomTempPublisherConf":
        return get_conf(
            RandomTempPublisherConf,
            ENV_VAR_PREFIX,
            file_path,
            nested_env_conf_separator="__",
        )
