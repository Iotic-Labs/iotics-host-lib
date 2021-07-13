import re

from iotics.lib.identity.api.high_level_api import get_rest_high_level_identity_api,\
    RegisteredIdentity, HighLevelIdentityApi
from iotics.lib.identity.error import IdentityResolverCommunicationError

from iotics.host.exceptions import DataSourcesAuthException


class AgentAuth:
    def __init__(
        self, api: HighLevelIdentityApi, user_did: RegisteredIdentity,
        agent_did: RegisteredIdentity, agent_seed: str
    ):
        self._api = api
        self._user_did = user_did
        self._agent_did = agent_did
        self._agent_seed = agent_seed

    def make_agent_auth_token(self, duration: int = 600) -> str:
        """make_agent_auth_token:
        duration = int seconds
        """
        return self._api.create_agent_auth_token(
            agent_registered_identity=self._agent_did,
            user_did=self._user_did.did,
            duration=duration
        )

    def make_twin_id(self, twin_key_name: str) -> str:
        """make_twin_id: Make and register a twin identity.  Return identifier.
        twin_key_name = along with a seed forms the DID

        Returns RegisteredIdentity
        """

        twin_did = self._api.create_twin_with_control_delegation(
            twin_seed=bytes.fromhex(self._agent_seed),
            twin_key_name=twin_key_name,
            agent_registered_identity=self._agent_did,
            delegation_name='#ControlDeleg', override_doc=True
        )

        return twin_did.did


class AgentAuthBuilder:

    @staticmethod
    def build_agent_auth(
        resolver_url: str, user_seed: str, user_key_name: str,
        agent_seed: str, agent_key_name: str,
        user_name: str = None, agent_name: str = None
    ) -> AgentAuth:
        """creates the class that can generate api tokens and twin dids for this agent

        Args:
            resolver_url (str): address of resolver
            user_seed (str): user seed
            user_key_name (str): along with the user seed this is used to generate
                the user DID can be any string any length as it is hashed
            agent_seed (str): agent seed
            agent_key_name (str): along with the agent seed this is used to generate
                the user DID can be any string any length as it is hashed
            user_name (str): optional friendly name that is stored in the DID document
            agent_name (str): optional friendly name that is stored in the DID document

        Returns:
            AgentAuth: class that can generate api tokens and twin dids for this agent
        """

        if (
            re.match(r'^[0-9a-fA-F]{32,64}$', user_seed) is None
            or re.match(r'^[0-9a-fA-F]{32,64}$', agent_seed) is None
        ):
            raise DataSourcesAuthException('Seeds must be hex string 32-64 chars')

        api = get_rest_high_level_identity_api(resolver_url)

        try:
            user_did, agent_did = api.create_user_and_agent_with_auth_delegation(
                user_seed=bytes.fromhex(user_seed), user_key_name=user_key_name, user_name=user_name,
                agent_seed=bytes.fromhex(agent_seed), agent_key_name=agent_key_name, agent_name=agent_name,
                delegation_name='#AuthDeleg'
            )
        except IdentityResolverCommunicationError as err:
            raise DataSourcesAuthException(err) from err

        return AgentAuth(api, user_did, agent_did, agent_seed)
