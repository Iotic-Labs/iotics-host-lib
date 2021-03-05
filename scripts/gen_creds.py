#!/usr/bin/env python3
import os
import sys
from pathlib import Path

if sys.version_info < (3, 8):
    print('Unexpected Python version, recommended version: 3.8', file=sys.stderr)

try:
    from iotic.lib.identity import Document, Identifier
    from iotic.lib.identity.client import IdentityClient
    from iotic.lib.identity.exceptions import IdentityNotFound
except ModuleNotFoundError as err:
    if err.name not in ['iotic', 'iotic.lib', 'iotic.lib.identity']:
        raise

    print('Missing Iotics dependency, try `pip install -f deps iotic.lib.identity`.', file=sys.stderr)
    exit(1)

NEW_SEED_LEN = 256  # 128 or 256
RESOLVER = os.getenv('RESOLVER') or 'http://localhost:5000'
SEED_CACHE_FILE = Path('user_seed.txt')


def main():
    check_resolver()
    if not SEED_CACHE_FILE.is_file():
        answer = input('Creating a new user seed, continue? [y]: ')
        if answer != 'y':
            return

    user_seed, created = get_or_create_user_seed()
    if created:
        store_seed(user_seed)
    else:
        print(f'Using an existing user seed from `{SEED_CACHE_FILE.absolute()}`.')

    user_doc, _ = get_or_create_user_identity(user_seed)
    answer = input('Creating a new agent seed, continue? [y]: ')
    if answer != 'y':
        return

    agent_seed = create_agent(user_doc)
    print('A new agent has been created, use the following variables for your connector:\n')
    print(f'export RESOLVER_HOST={RESOLVER}')
    print(f'export HOST_USER={user_doc.id}')
    print(f'export SEED={agent_seed}')
    print('\nRemember to store the above values as you may loose control of your connectors otherwise.')


def check_resolver():
    if os.getenv('RESOLVER'):
        print(f'A simple helper script to generate DIDs and seeds using `{RESOLVER}` resolver.')
    else:
        print(f'`RESOLVER` environment variable not found, defaulting to `{RESOLVER}`.')
        os.environ['RESOLVER'] = RESOLVER


def get_or_create_user_seed():
    """Creates a random or finds an existing seed for a project (used to create user/agent DIDs)."""
    created = False
    if SEED_CACHE_FILE.is_file():
        with SEED_CACHE_FILE.open() as f:
            seed = f.readline()
    else:
        seed = Identifier.new_seed(NEW_SEED_LEN)
        created = True
    return seed, created


def store_seed(seed):
    """Stores project seed for a later use, to create more agents for the same user."""
    print(f'A new user has been created for seed: `{seed}`.')
    print('Remember that the seed is your secret value, you should keep it safe and secure!')
    answer = input(f'Do you want to store the seed in `{SEED_CACHE_FILE.absolute()}` for later use? [y]: ')
    if answer == 'y':
        SEED_CACHE_FILE.write_text(seed)
        print('It is NOT advised to store a seed in a file on a production environment.')


def get_or_create_user_identity(user_seed):
    """Creates a new or finds an existing user identity (DID)."""
    user_doc, created, _ = _get_doc(Identifier.DIDType.USER, user_seed)
    return user_doc, created


def create_agent(user_doc):
    """Returns a seed and creates an agent (DID) if agent with given name does not exist."""
    agent_seed = Identifier.new_seed(NEW_SEED_LEN)
    agent_doc, _, private_key = _get_doc(Identifier.DIDType.AGENT, agent_seed)

    proof = Document.new_proof(user_doc.id.encode('ascii'), private_key)
    delegation = Document.new_delegation('#agent', agent_doc.id + agent_doc.public_keys[0].id, proof)
    user_doc.add_authentication_delegation(delegation)

    return agent_seed


def _get_doc(did_type, seed_str):
    """Creates a new or finds an existing user/agent identity."""
    seed = Identifier.seed_to_master(seed_str)
    private_key_hex = Identifier.new_private_hex_from_path(seed, did_type, count=0)
    private_key_ecdsa = Identifier.private_hex_to_ECDSA(private_key_hex)
    doc = Document.new_did_document(did_type, private_key_ecdsa)
    did = doc.id
    identity_client = IdentityClient()
    try:
        doc = identity_client.discover(did)
    except IdentityNotFound:
        token = Document.new_document_token(doc, RESOLVER, did + doc.public_keys[0].id, private_key_ecdsa)
        identity_client.register(token)
        created = True
    else:
        created = False

    return doc, created, private_key_ecdsa


if __name__ == '__main__':
    main()
