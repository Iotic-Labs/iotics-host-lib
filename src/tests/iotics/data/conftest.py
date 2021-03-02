import pytest

from iotics.host.api.qapi import QApiFactory
from iotics.host.conf.base import DataSourcesConfBase
from tests.iotics.data.mocks import AgentAuthTest, get_api_exception


@pytest.fixture
def twin_id():
    return 'did:iotic:atesttwinid'


@pytest.fixture
def feed_id():
    return 'a feed id'


@pytest.fixture
def twin_api():
    return QApiFactory(DataSourcesConfBase(), AgentAuthTest()).get_twin_api()


@pytest.fixture
def api_exception():
    return get_api_exception()
