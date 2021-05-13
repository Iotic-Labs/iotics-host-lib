from uuid import uuid4
from iotics.host.auth import AgentAuthBuilder
from iotics.host.api.qapi import QApiFactory

from iotics.host.conf.base import AuthConf, DataSourcesConfBase, get_conf
from iotics.host.exceptions import DataSourcesQApiError

ENV_VAR_PREFIX = 'HELPER_'

class HelperConf(DataSourcesConfBase):
    auth: AuthConf

    @staticmethod
    def get_conf(file_path: str = None) -> 'HelperConf':
        return get_conf(HelperConf, ENV_VAR_PREFIX, file_path, nested_env_conf_separator='__')


def main():
    conf = HelperConf.get_conf()

    agent_auth = AgentAuthBuilder.build_agent_auth(conf.auth.resolver_host, conf.auth.seed, conf.auth.user)
    qapi_factory = QApiFactory(conf, agent_auth, client_app_id=f'del_helper_{uuid4()}')

    twin_api = qapi_factory.get_twin_api()

    resp = twin_api.list_twins()

    if not resp or not resp.twins:
        print('No twins found')
        return

    allow = input(f'Are you sure you want to delete {len(resp.twins)} twins on {conf.qapi_url}? Y/n: ')

    if allow != 'Y':
        print('No twins deleted')
        return

    del_count = 0

    try:
        for twin in resp.twins:
            try:
                del_resp = twin_api.delete_twin(twin.id.value)
            except DataSourcesQApiError as ex:
                if ex.http_error.status == 403:
                    print(f'Not allowed to delete {twin.id.value}. {ex.http_error.body}')
                    continue
                raise

            assert del_resp.twin.id.value == twin.id.value
            del_count += 1
    except:
        print(f'{del_count} twins deleted')
        raise

    print(f'{del_count} twins deleted')


if __name__ == '__main__':
    main()
