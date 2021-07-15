#!/usr/bin/env python
"""make_twin: Make a new Twin ID using agent seed and register it with the resolver"""

import os
import sys

from iotics.lib.identity.api.high_level_api import get_rest_high_level_identity_api


def main():

    resolver = os.environ.get('RESOLVER_HOST')

    user_seed = os.environ.get('USER_SEED')
    user_key_name = os.environ.get('USER_KEY_NAME')

    agent_seed = os.environ.get('AGENT_SEED')
    agent_key_name = os.environ.get('AGENT_KEY_NAME')

    if not all([resolver, user_key_name, user_seed, agent_key_name, agent_seed]):
        print('Error: RESOLVER_HOST, USER_KEY_NAME, USER_SEED, AGENT_KEY_NAME and AGENT_SEED must all be set')
        sys.exit(1)

    api = get_rest_high_level_identity_api(resolver)

    _, agent_registered_id = api.create_user_and_agent_with_auth_delegation(
        user_seed=bytes.fromhex(user_seed), user_key_name=user_key_name,
        agent_seed=bytes.fromhex(agent_seed), agent_key_name=agent_key_name,
        delegation_name='#AuthDeleg'
    )

    try:
        twin_num = int(sys.argv[1])
    except (IndexError, ValueError):
        print('usage: ./make_twin.py 1 <-- number required. Used for key number')
        sys.exit(1)

    twin_seed, twin_key_name, twin_name = bytes.fromhex(agent_seed), f'#MyTwin{twin_num}Key', f'#MyTwin{twin_num}Name'

    twin_registered_id = api.create_twin_with_control_delegation(
        twin_seed=twin_seed, twin_key_name=twin_key_name, twin_name=twin_name,
        agent_registered_identity=agent_registered_id,
        delegation_name='#ControlDeleg'
    )

    print(f'Twin ID: {twin_registered_id.did}')


if __name__ == '__main__':
    main()
