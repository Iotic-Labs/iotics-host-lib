#!/usr/bin/env python3
"""A helper script for generating credentials for agents (connectors)."""
import os
import secrets
import string
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
    sys.exit(1)


def main():
    cred_gen = CredentialsGenerator()
    user_seed, created = cred_gen.get_or_create_user_seed()
    if created:
        cred_gen.store_seed(user_seed)

    user_doc = cred_gen.get_or_create_user_identity(user_seed)
    agent_seed = cred_gen.create_agent(user_doc, user_seed)

    print('A new agent has been created, use the following variables for your connector:\n')
    print(f'export RESOLVER_HOST={cred_gen.resolver_address}')
    print(f'export HOST_USER={user_doc.id}')
    print(f'export SEED={agent_seed}')
    print('\nRemember to store the above values as you may loose control of your connectors otherwise.')


class CredentialsGenerator:
    new_seed_len = 256  # 128 or 256
    seed_cache_file = 'user_seed.txt'

    def __init__(self):
        self.resolver_address = os.getenv('RESOLVER') or 'http://localhost:5000'
        if os.getenv('RESOLVER'):
            print(f'A simple helper script to generate DIDs and seeds using `{self.resolver_address}` resolver.')
        else:
            print(f'`RESOLVER` environment variable not found, defaulting to `{self.resolver_address}`.')
            os.environ['RESOLVER'] = self.resolver_address

        self.identity_client = IdentityClient()
        self.seed_cache = Path(self.seed_cache_file)

    def get_or_create_user_seed(self):
        """Creates a random or finds an existing user seed (used to create user/agent DIDs).

        Returns:
            tuple: A seed and True if it was created or False otherwise.
        """
        if not self.seed_cache.is_file():
            self.continue_prompt('Creating a new user seed')
            seed = Identifier.new_seed(self.new_seed_len)
            return seed, True

        with self.seed_cache.open() as f:
            seed = f.readline()
        print(f'Found a user seed in `{self.seed_cache.absolute()}`.')
        try:
            assert int(seed, 16)
        except ValueError:
            raise ValueError('The seed is not of a hex value.')
        if not len(seed) in (32, 64):
            raise ValueError('The seed has incorrect length.')

        return seed, False

    def store_seed(self, seed):
        """Stores given user seed for a later use, i.e. to create more agents for the same user."""
        print(f'A new user seed has been generated: `{seed}`.')
        print('Remember that this USER SEED is your secret value, and it should be kept safe and secure!')
        answer = input(f'Do you want to store the seed in `{self.seed_cache.absolute()}` for later use? [y]: ')
        if answer == 'y':
            self.seed_cache.write_text(seed)
            print(
                'It is NOT recommended to store USER SEED on a production environment!'
                ' Instead it should be kept safe and secure elsewhere.')

    def get_or_create_user_identity(self, user_seed):
        """Creates a new or finds an existing user identity (DID)."""
        user_doc, created, _ = self._get_doc(Identifier.DIDType.USER, user_seed)
        if created:
            print('A new user DID has been created.')
        return user_doc

    def create_agent(self, user_doc, user_seed):
        """Creates an agent (DID) for given user and returns its secret seed."""
        self.continue_prompt('Creating a new agent')

        agent_seed = Identifier.new_seed(self.new_seed_len)
        agent_doc, _, private_key = self._get_doc(Identifier.DIDType.AGENT, agent_seed)

        # Authorising a new agent requires a delegation to be added to the user_doc.
        issuer = agent_doc.id + agent_doc.public_keys[0].id
        proof = Document.new_proof(user_doc.id.encode('ascii'), private_key)
        dname = '#agent_' + ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(6))
        delegation = Document.new_delegation(dname, issuer, proof)
        user_doc.add_authentication_delegation(delegation)

        # Updates to DID documents must be registered on the resolver.
        user_private_ecdsa = self._seed_to_private_key(user_seed, Identifier.DIDType.USER)
        self._register_doc(user_doc, user_private_ecdsa, overwrite=True)

        return agent_seed

    @staticmethod
    def continue_prompt(text):
        answer = input(f'{text}, continue? [y]: ')
        if answer != 'y':
            sys.exit()

    def _get_doc(self, did_type, seed):
        """Creates a new or finds an existing user/agent identity."""
        private_key_ecdsa = self._seed_to_private_key(seed, did_type)
        doc = Document.new_did_document(did_type, private_key_ecdsa)
        return self._register_doc(doc, private_key_ecdsa)

    def _seed_to_private_key(self, seed, did_type):
        """Creates a private ECDSA key instance for given a seed (hex) and DID Type."""
        master = Identifier.seed_to_master(seed)
        private_key_hex = Identifier.new_private_hex_from_path(master, did_type, count=0)
        private_key_ecdsa = Identifier.private_hex_to_ECDSA(private_key_hex)
        return private_key_ecdsa

    def _register_doc(self, doc, private_key_ecdsa, overwrite=False):
        """Creates or updates a document in the resolver.

        Returns:
            tuple: A document; True if created and False otherwise; related ECDSA private key.
        """
        issuer = doc.id + doc.public_keys[0].id

        found = True
        try:
            found_doc = self.identity_client.discover(issuer)
        except IdentityNotFound:
            found = False
        else:
            if not overwrite:
                return found_doc, False, private_key_ecdsa

        token = Document.new_document_token(doc, self.resolver_address, issuer, private_key_ecdsa)
        self.identity_client.register(token)
        created = True if not found else False
        return doc, created, private_key_ecdsa


if __name__ == '__main__':
    main()
