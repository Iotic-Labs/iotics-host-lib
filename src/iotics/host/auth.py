import os
import re
from collections import namedtuple
from typing import Optional

import requests
from iotic.lib.identity import Authentication, Document, Identifier, Resolver
from iotic.lib.identity.document import DIDDocument, RESOLVER_ENV
from iotic.lib.identity.exceptions import IdentityNotFound

from iotics.host.exceptions import DataSourcesAuthException

Agent = namedtuple('Agent', ('id', 'pk', 'doc'))


class AgentAuth:
    """AgentAuth: A very basic auth helper for an agent & twins

    Caveats:
    - Twins should be made using a path on the Agent seed (not their own seed)
    - Agent & Twins will use the first public key (eg keys not rotated)
    """

    # DEFAULT_DELEG_NAME Used when delegating twin -> agent.
    DEFAULT_DELEG_NAME = '#agent'

    def __init__(self, agent: Agent, master: bytes, user_deleg: str, user_id: str, audience: str):
        self.audience = audience
        self.user_id = user_id
        self.master = master
        self.agent = agent
        self.user_deleg = user_deleg

    def make_agent_auth_token(self, audience: str = 'test-audience', duration: int = 600) -> str:
        """make_agent_auth_token:
        audience = address or ID (not enforced by iotic-web/rest currently)
        duration = int seconds
        """
        # future to do: might not be public_keys[0] ?
        issuer = self.agent.doc.id + self.agent.doc.public_keys[0].id

        tkn = Authentication.new_authentication_token(
            issuer,                     # Issuer is Agent
            self.user_id,               # Subject is User we're authenticating as
            audience,                   # Audience is the id/address/url we're authenticating to
            duration,                   # Duration seconds
            self.agent.pk
        )
        return tkn.decode('ascii')

    def make_twin_id(self, lid: str, agent_deleg: bool = True) -> tuple:
        """make_twin_id: Make and register a twin identity.  Return identifier.
        lid = twin local id
        agent_deleg = Optional True/False to delegate to (this) Agent

        Returns did, private_key_ecdsa, doc
        """
        pk_hex = Identifier.new_private_hex_from_path_str(self.master, Identifier.DIDType.TWIN, lid)
        prk = Identifier.private_hex_to_ECDSA(pk_hex)
        doc = Document.new_did_document(Identifier.DIDType.TWIN, prk)

        if not discover_identity(doc.id):
            if agent_deleg:
                proof = Document.new_proof(doc.id.encode('ascii'), self.agent.pk)
                deleg = Document.new_delegation(self.DEFAULT_DELEG_NAME,
                                                self.agent.id + self.agent.doc.public_keys[0].id,
                                                proof)
                doc.add_control_delegation(deleg)

            tkn = Document.new_document_token(doc, self.audience, doc.id + doc.public_keys[0].id, prk)
            Resolver.register(tkn)

        return doc.id, prk, doc


def discover_identity(did) -> Optional[DIDDocument]:
    """Fetch and return DDO or None"""
    try:
        return Resolver.discover(did)
    except IdentityNotFound:
        return None
    except requests.RequestException as err:
        raise DataSourcesAuthException(err) from err


class AgentAuthBuilder:
    @staticmethod
    def _get_agent_id_from_private_key(master: bytes, keynum: int = 0):
        pk_hex = Identifier.new_private_hex_from_path(master, Identifier.DIDType.AGENT, keynum)
        prk = Identifier.private_hex_to_ECDSA(pk_hex)
        puk = Identifier.private_ECDSA_to_public_ECDSA(prk)
        puk_hex = Identifier.public_ECDSA_to_bytes(puk).hex()
        agent_id = Identifier.make_identifier(puk_hex)
        return agent_id, prk

    @staticmethod
    def _get_user_deleg(user_id: str, agent_id: str):
        """Check the agent is allowed to work on user's behalf

        Returns the name of the delegation used for user -> agent
        """
        user_doc = discover_identity(user_id)
        if user_doc is None:
            raise DataSourcesAuthException(f'User ID {user_id} does not exist')

        for k in user_doc.delegate_control + user_doc.delegate_authentication:
            if Identifier.compare_identifier_only(agent_id, k.controller):
                return k.id

        raise DataSourcesAuthException(f'User ID {user_id} has not allowed Agent {agent_id}')

    @staticmethod
    def _get_agent(master: bytes, keynum: int = 0) -> Agent:
        agent_id, prk = AgentAuthBuilder._get_agent_id_from_private_key(master, keynum)
        agent_doc = discover_identity(agent_id)
        if not agent_doc:
            raise DataSourcesAuthException(f'Agent ID {agent_id} does not exist')

        return Agent(agent_id, prk, agent_doc)

    @staticmethod
    def build_agent_auth(host: str,
                         seed: str,
                         user_id: str,
                         password: bytes = b'',
                         method: int = Identifier.SeedMethod.SEED_METHOD_BIP39,
                         keynum: int = 0) -> AgentAuth:
        """
        seed = hex string
        user_id = DID of user this agent is working on behalf of
        password = optional bytes
        """
        os.environ[RESOLVER_ENV] = host
        if re.match(r'^[0-9a-fA-F]{32,64}$', seed) is None:
            raise DataSourcesAuthException('Seed must be hex string 32-64 chars')
        try:
            Identifier.validate_identifier(user_id)
        except ValueError as err:
            raise DataSourcesAuthException(err) from err
        master = Identifier.seed_to_master(seed, password, method)
        agent = AgentAuthBuilder._get_agent(master, keynum)
        user_deleg = AgentAuthBuilder._get_user_deleg(user_id, agent.id)
        return AgentAuth(agent, master, user_deleg, user_id, audience=host)
