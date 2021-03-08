#!/usr/bin/env python
"""make_auth: Generates an Agent Auth Token using the environment variables printed by gen_creds.py"""

import os

from iotic.lib.identity import Identifier, Authentication


def main():
    audience = os.environ.get('RESOLVER_HOST', 'audience')
    user_id = os.environ.get('HOST_USER')
    agent_seed = os.environ.get('SEED')
    if not user_id or not agent_seed:
        print('Error: Must set HOST_USER and SEED environment variables from gen_creds.py')

    master = Identifier.seed_to_master(agent_seed)
    private_key_hex = Identifier.new_private_hex_from_path(master, Identifier.DIDType.AGENT, count=0)
    private_key_ecdsa = Identifier.private_hex_to_ECDSA(private_key_hex)

    public_key_ecdsa = Identifier.private_ECDSA_to_public_ECDSA(private_key_ecdsa)
    public_key_hex = Identifier.public_ECDSA_to_bytes(public_key_ecdsa).hex()
    issuer = Identifier.make_identifier(public_key_hex) + '#agent-0'

    print(f'---\nNew Authentication Token for Agent: {issuer}\n')

    print(Authentication.new_authentication_token(issuer,
                                                  user_id,
                                                  audience,
                                                  60 * 60 * 8,         # 8hr duration
                                                  private_key_ecdsa).decode())


if __name__ == '__main__':
    main()
