#!/usr/bin/env python3
import os
import sys
from pathlib import Path

if sys.version_info < (3, 8):
    print('Unexpected Python version, recommended version: 3.8', file=sys.stderr)

try:
    from iotic.lib.identity import Document, Identifier, Resolver
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
    if os.getenv('RESOLVER'):
        print(f'A simple helper script to generate DIDs and seeds using `{RESOLVER}` resolver.')
    else:
        print(f'`RESOLVER` environment variable not found, defaulting to `{RESOLVER}`.')
        os.environ['RESOLVER'] = RESOLVER
    if not SEED_CACHE_FILE.is_file():
        answer = input('Creating a new user seed, continue? [y]: ')
        if answer != 'y':
            return

    project_seed, created = get_or_create_project_seed()
    if created:
        store_seed(project_seed)
    else:
        print(f'Using an existing user seed from `{SEED_CACHE_FILE.absolute()}`.')

    user_did, _ = get_or_create_user_identity(project_seed)
    name = input('Creating a seed for an agent, provide a name for your agent (e.g.: `agent-follower` or leave empty to abort): ')
    if not name:
        return

    agent_seed = create_agent(project_seed, name)
    if not agent_seed:
        print('An agent for the given user seed and name already exists.')
        return

    print('A new agent has been created, use the following variables for your connector:\n')
    print(f'export RESOLVER_HOST={RESOLVER}')
    print(f'export HOST_USER={user_did}')
    print(f'export SEED={agent_seed}')
    print('\nRemember to store the above values as you may loose control of your connectors otherwise.')


def get_or_create_project_seed():
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


def get_or_create_user_identity(project_seed):
    """Creates a new or finds an existing user identity (DID)."""
    did, created = _get_doc(Identifier.DIDType.USER, project_seed)
    return did, created


def create_agent(project_seed, name):
    """Returns a seed and creates an agent (DID) if agent with given name does not exist."""
    if name and not name.startswith('#'):
        name = '#' + name
    did, created = _get_doc(Identifier.DIDType.AGENT, project_seed, name)
    if not created:
        return

    agent_seed = Identifier.new_seed(NEW_SEED_LEN)
    return agent_seed


def _get_doc(did_type, project_seed, name=None):
    """Creates a new or finds an existing user/agent identity."""
    seed = Identifier.seed_to_master(project_seed)
    if not name:
        private_key_hex = Identifier.new_private_hex_from_path(seed, did_type, count=0)
    else:
        private_key_hex = Identifier.new_private_hex_from_path_str(seed, did_type, name)
    private_key_ecdsa = Identifier.private_hex_to_ECDSA(private_key_hex)
    doc = Document.new_did_document(did_type, private_key_ecdsa, name or '')
    did = doc.id
    try:
        doc = Resolver.discover(did)
    except IdentityNotFound:
        tkn = Document.new_document_token(doc, RESOLVER, did + doc.public_keys[0].id, private_key_ecdsa)
        Resolver.register(tkn)
        created = True
    else:
        created = False

    return doc.id, created


if __name__ == '__main__':
    main()
