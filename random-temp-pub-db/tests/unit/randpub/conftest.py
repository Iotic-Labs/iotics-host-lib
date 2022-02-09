import tempfile
import pytest
from iotics.host.conf.base import AuthConf
from randpub.conf import RandomTempPublisherConf


@pytest.fixture
def work_dir():
    """
        Provide a temporary work directory for test as a fixture.
        Create and return a unique temporary directory which is automatically removed at the end
        of the test.
    """
    with tempfile.TemporaryDirectory() as work_dir:
        yield work_dir


@pytest.fixture
def conf():
    return RandomTempPublisherConf(
        auth=AuthConf(seed='aaa', user='did:iotics:bbbb', resolver_host='http://plop'),
        ext_endpoint_base='http://plop', api_key='12'
    )
