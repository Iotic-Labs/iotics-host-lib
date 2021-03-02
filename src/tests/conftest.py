import tempfile

import pytest


@pytest.fixture
def work_dir():
    """
        Provide a temporary work directory for test as a fixture.
        Create and return a unique temporary directory which is automatically removed at the end
        of the test.
    """
    with tempfile.TemporaryDirectory() as work_dir:
        yield work_dir
