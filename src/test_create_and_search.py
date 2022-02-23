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
from random import randint

from iotics.host.auth import AgentAuthBuilder
from iotics.host.api.qapi import QApiFactory
from iotics.host.conf.base import DataSourcesConfBase
from iotic.lib.identity.identifier import SeedMethod
from iotic.web.rest.client.qapi import Scope, Visibility


# Create the necessary api instances.
print("This script requires locally-running host instances with qapi on ports 8081 and 8091, "
      "and identities created with get_debug_auth.py")
agent_auth = AgentAuthBuilder.build_agent_auth(
    "http://localhost:5000",
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM#user-0",
    method=SeedMethod.SEED_METHOD_BIP39
)
qapi_factory = QApiFactory(DataSourcesConfBase(), agent_auth)
qapi_factory_remote = QApiFactory(DataSourcesConfBase(qapi_url='http://localhost:8091/qapi'), agent_auth)

twin_api_local = qapi_factory.get_twin_api()
twin_api_remote = qapi_factory_remote.get_twin_api()
feed_api_local = qapi_factory.get_feed_api()
feed_api_remote = qapi_factory_remote.get_feed_api()
search_api = qapi_factory.get_search_api()

# Show any entities that may be present from previous runs of this script, or matching the same tag.
tag = 'tag'
timeout = int(input('Timeout? (10s) ') or 10)
print("Preexisting entities on hosts:")
results_local = search_api.search_twins(text=tag, scope=Scope.LOCAL, timeout=timeout)
results_total = search_api.search_twins(text=tag, scope=Scope.GLOBAL, timeout=timeout)

print("Local: %s" % sum([len(resp.twins) for resp in list(results_local)]))
print("Total: %s" % sum([len(resp.twins) for resp in list(results_total)]))
if results_total:
    print("You may wish to kill this script and try with a fresh host.")

# Get desired entity counts for create and search test.
default = randint(1, 51)
entites_local = int(input("Entities to create locally? (%s) " % default) or default)
default = randint(1, 51)
entites_remote = int(input("Entities to create remotely? (%s) " % default) or default)

# Create entities with the given tag.
point_name = 'point'
print("Creating %s local entities" % entites_local)
for i in range(entites_local):
    entity_name = 'local_entity_%d' % i
    print(entity_name, end='\r', flush=True)
    entity_id, _, _ = agent_auth.make_twin_id(entity_name)
    twin_api_local.create_twin(entity_id)
    twin_api_local.update_twin(entity_id, add_tags=[tag])
    feed_api_local.create_feed(entity_id, point_name)
print("Creating %s remote entities" % entites_remote)
for i in range(entites_remote):
    entity_name = 'remote_entity_%d' % i
    print(entity_name, end='\r', flush=True)
    entity_id, _, _ = agent_auth.make_twin_id(entity_name)
    twin_api_remote.create_twin(entity_id)
    twin_api_remote.update_twin(entity_id, add_tags=[tag], new_visibility=Visibility.PUBLIC)
    feed_api_remote.create_feed(entity_id, point_name)

# Make sure all entities created in the previous step can be found.
results_local = search_api.search_twins(text=tag, scope=Scope.LOCAL, timeout=timeout)
results_total = search_api.search_twins(text=tag, scope=Scope.GLOBAL, timeout=timeout)
print("Updated entities on hosts:")
print("Local (expected %s): %s" % (entites_local, sum([len(resp.twins) for resp in list(results_local)])))
print("Total: (expected %s): %s" % (entites_local + entites_remote, sum([len(resp.twins) for resp in list(results_total)])))
