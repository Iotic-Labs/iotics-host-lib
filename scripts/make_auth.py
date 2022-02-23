#!/usr/bin/env python
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
"""make_auth: Generates an Agent Auth Token using the environment variables printed by gen_creds.py"""

import os
import sys

from iotics.lib.identity.api.high_level_api import get_rest_high_level_identity_api


def main():

    resolver = os.environ.get('RESOLVER_HOST')

    user_key_name = os.environ.get('USER_KEY_NAME')
    user_seed = os.environ.get('USER_SEED')

    agent_key_name = os.environ.get('AGENT_KEY_NAME')
    agent_seed = os.environ.get('AGENT_SEED')

    if not all([resolver, user_key_name, user_seed, agent_key_name, agent_seed]):
        print('Error: RESOLVER_HOST, USER_KEY_NAME, USER_SEED and AGENT_KEY_NAME must all be set')
        sys.exit(1)

    api = get_rest_high_level_identity_api(resolver)

    user_registered_id, agent_registered_id = api.create_user_and_agent_with_auth_delegation(
        user_seed=bytes.fromhex(user_seed), user_key_name=user_key_name,
        agent_seed=bytes.fromhex(agent_seed), agent_key_name=agent_key_name,
        delegation_name='#AuthDeleg'
    )

    # -- Create token -------------------------------------------------------------------------------------------------- #

    print(f'---\nNew Authentication Token for Agent: {agent_registered_id.did}\n')

    print(api.create_agent_auth_token(
        agent_registered_identity=agent_registered_id,
        user_did=user_registered_id.did, duration=3600
    ))


if __name__ == '__main__':
    main()
