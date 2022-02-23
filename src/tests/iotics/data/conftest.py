# Copyright 2022 Iotic Labs Ltd.
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
