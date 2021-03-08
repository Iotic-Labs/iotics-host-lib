#!/usr/bin/env python
"""make_twin: Make a new Twin ID using agent seed and register it with the resolver"""

import os
import sys

from iotic.lib.identity import Identifier, IdentityClient, Document
from iotic.lib.identity.resolver import HttpResolverClient


def main():
    if not os.environ.get('RESOLVER_HOST'):
        print('Error: RESOLVER_HOST environment must be set')
        sys.exit(1)

    audience = os.environ.get('RESOLVER_HOST', 'audience')
    agent_seed = os.environ.get('SEED')
    if not agent_seed:
        print('Error: Must set SEED environment variable from gen_creds.py')
        sys.exit(1)

    try:
        twin_num = int(sys.argv[1])
    except (IndexError, ValueError):
        print('usage: ./make_twin.py 1 <-- number required. Used for key number')
        sys.exit(1)

    master = Identifier.seed_to_master(agent_seed)

    # Shortcut to get the agent ID needed for delegation
    private_key_hex = Identifier.new_private_hex_from_path(master, Identifier.DIDType.AGENT, count=0)
    agent_private_key_ecdsa = Identifier.private_hex_to_ECDSA(private_key_hex)
    agent_doc = Document.new_did_document(Identifier.DIDType.AGENT, agent_private_key_ecdsa)

    # Create the Twin Keys from Agent Seed and command line number
    private_key_hex = Identifier.new_private_hex_from_path(master, Identifier.DIDType.TWIN, count=twin_num)
    twin_private_key_ecdsa = Identifier.private_hex_to_ECDSA(private_key_hex)

    twin_doc = Document.new_did_document(Identifier.DIDType.TWIN, twin_private_key_ecdsa)

    # Allow the Agent to control this Twin
    proof = Document.new_proof(twin_doc.id.encode('ascii'), agent_private_key_ecdsa)
    delegation = Document.new_delegation('#agent', agent_doc.id + agent_doc.public_keys[0].id, proof)
    twin_doc.add_control_delegation(delegation)

    issuer = twin_doc.id + twin_doc.public_keys[0].id
    token = Document.new_document_token(twin_doc,
                                        audience,
                                        issuer,
                                        twin_private_key_ecdsa)

    resolver = HttpResolverClient(audience)
    idc = IdentityClient(resolver)
    idc.register(token)

    print(f'Twin ID: {twin_doc.id}')


if __name__ == '__main__':
    main()
