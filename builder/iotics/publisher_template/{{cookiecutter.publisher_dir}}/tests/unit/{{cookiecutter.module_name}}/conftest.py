# Copyright © 2021 to 2022 IOTIC LABS LTD. info@iotics.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Iotic-Labs/iotics-host-lib/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import tempfile
import pytest
from iotics.host.conf.base import AuthConf
from {{cookiecutter.module_name}}.conf import {{cookiecutter.publisher_class_name}}Conf


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
    return {{cookiecutter.publisher_class_name}}Conf(
        auth=AuthConf(seed='aaa', user='did:iotics:bbbb', resolver_host='http://plop'),
        ext_endpoint_base='http://plop', api_key='12'
    )
