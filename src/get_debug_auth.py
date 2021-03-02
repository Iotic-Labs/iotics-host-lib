import os

from iotic.lib.identity import Document, Identifier, Resolver
from iotic.lib.identity.exceptions import IdentityNotFound

DEBUG_AGENT_SEED = os.environ.get('DEBUG_SEED', 'a' * 32)
DEBUG_AGENT_KEYNAME = '#agent-0'

DEBUG_USER_SEED = os.environ.get('DEBUG_SEED', 'b' * 32)
DEBUG_USER_KEYNAME = '#user-0'
DEBUG_USER_DELEG = '#testagent'


def make_private_key(seed, doc_type, count):
    mad = Identifier.seed_to_master(seed)
    pk_hex = Identifier.new_private_hex_from_path(mad, doc_type, count)
    return Identifier.private_hex_to_ECDSA(pk_hex)


def check_identity_exists(did):
    try:
        Resolver.discover(did)
    except IdentityNotFound:
        return False
    return True


def setup_id():
    """setup_test_identity: Make a bunch of test identities"""
    agent_pk = make_private_key(DEBUG_AGENT_SEED, Identifier.DIDType.AGENT, 0)
    agent_doc = Document.new_did_document(Identifier.DIDType.AGENT, agent_pk)
    agent_iss = agent_doc.id + DEBUG_AGENT_KEYNAME

    if not check_identity_exists(agent_doc.id):
        tkn = Document.new_document_token(agent_doc, "unit-test", agent_iss, agent_pk)
        Resolver.register(tkn)

    user_pk = make_private_key(DEBUG_USER_SEED, Identifier.DIDType.USER, 0)
    user_doc = Document.new_did_document(Identifier.DIDType.USER, user_pk)
    user_iss = user_doc.id + DEBUG_USER_KEYNAME

    proof = Document.new_proof(user_doc.id.encode('ascii'), agent_pk)
    deleg = Document.new_delegation(DEBUG_USER_DELEG, agent_iss, proof)
    user_doc.add_authentication_delegation(deleg)

    if not check_identity_exists(user_doc.id):
        tkn = Document.new_document_token(user_doc, "unit-test", user_iss, user_pk)
        Resolver.register(tkn)

    return agent_iss, user_iss


def get_auth_debug():
    """Make a debug identities"""
    _, user_iss = setup_id()
    print('DEBUG identities:')
    print(f'SEED: {DEBUG_AGENT_SEED}')
    print(f'USER: {user_iss}')

if __name__ == '__main__':
    get_auth_debug()
