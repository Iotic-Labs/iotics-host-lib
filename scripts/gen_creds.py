#!/usr/bin/env python3
"""A helper script for generating credentials for agents (connectors)."""
import argparse
import sys
from pathlib import Path


if sys.version_info < (3, 8):
    print('Unexpected Python version, recommended version: 3.8', file=sys.stderr)

try:
    from iotics.lib.identity.api.high_level_api import get_rest_high_level_identity_api
except ModuleNotFoundError as err:
    if not err.name.startswith('iotics'):
        raise

    print('Missing Iotics dependency, try `pip install iotics-identity`.', file=sys.stderr)
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--resolver', help='Resolver address e.g. `https://did.prd.iotics.com`', default='http://localhost:5000')
    parser.add_argument(
        '--user_key_name', help='Along with the user seed forms part of the user\'s DID', default='00'
    )
    parser.add_argument(
        '--agent_key_name', help='Along with the agent seed forms part of the agent\'s DID', default='00'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    cred_gen = CredentialsGenerator(args.resolver)

    user_seed, user_key_name, created = cred_gen.get_or_create_user_seed(args.user_key_name)
    if created:
        cred_gen.store_secret(user_seed, user_key_name)

    agent_seed = cred_gen.create_agent()

    print('A new agent has been created, use the following variables for your connector:\n')
    print(f' export RESOLVER_HOST={cred_gen.resolver_address}')
    print(f' export USER_SEED={user_seed}')
    print(f' export USER_KEY_NAME={user_key_name}')
    print(f' export AGENT_SEED={agent_seed}')
    print(f' export AGENT_KEY_NAME={args.agent_key_name}')
    print('\nRemember to store the above values as you may loose control of your connectors otherwise.')
  

class CredentialsGenerator:
    seed_cache_file = 'user_secrets.txt'

    def __init__(self, resolver):
        self.resolver_address = resolver

        print(f'A simple helper script to generate DIDs and seeds using `{self.resolver_address}` resolver.')

        self.api = get_rest_high_level_identity_api(resolver_url=self.resolver_address)
        self.seed_cache = Path(self.seed_cache_file)

    def get_or_create_user_seed(self, user_key_name):
        """Creates a random or finds an existing user seed

        Returns:
            tuple: A seed, key_name and True if it was created or False otherwise.
        """
        if not self.seed_cache.is_file():
            self.continue_prompt('Creating a new user seed')
            seed = self.api.create_seed().hex()

            return seed, user_key_name, True

        with self.seed_cache.open() as f:
            user_secrets = f.readline()
        print(f'Found a user seed in `{self.seed_cache.absolute()}`.')

        parts = user_secrets.split(',')
        assert len(parts) == 2, 'expecting there to be 2 comma separated values in the seed file; seed,user_key_name'
        saved_seed = parts[0]
        saved_key_name = parts[1]
        assert int(saved_seed, 16), 'expecting the seed to be a hex value'
        assert saved_key_name, 'expecting user key name to be set in the user secrets file'

        if not len(saved_seed) in (32, 64):
            raise ValueError('The seed has incorrect length.')

        return saved_seed, saved_key_name, False

    def store_secret(self, seed, user_key_name):
        """Stores given user seed and user_key_name for a later use, i.e. to create more agents for the same user."""
        print(f'A new user seed has been generated: `{seed}` to be used in combination with user key name `{user_key_name}`.')
        print('Remember that this USER SEED and USER KEY NAME are your secret values, and should be kept safe and secure!')
        answer = input(f'Do you want to store the seed in `{self.seed_cache.absolute()}` for later use? [y/N]: ')
        if answer == 'y':
            self.seed_cache.write_text(f'{seed},{user_key_name}')
            print(
                'It is NOT recommended to store USER SEED and USER KEY NAME on a production environment!'
                ' Instead they should be kept safe and secure elsewhere.')

    def create_agent(self):
        """Creates an agent seed"""
        self.continue_prompt('Creating a new agent')

        seed = self.api.create_seed().hex()

        return seed

    @staticmethod
    def continue_prompt(text):
        answer = input(f'{text}, continue? [y/N]: ')
        if answer != 'y':
            sys.exit()


if __name__ == '__main__':
    main()
