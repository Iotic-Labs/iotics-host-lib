# Copyright © 2021 to 2022 IOTIC LABS LTD. info@iotics.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Iotic-Labs/iotics-host-lib/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from iotic.lib.identity import Document, Identifier, Resolver

TEST_AGENT_SEED = 'a' * 32
TEST_AGENT_ID = 'did:iotics:iotNypxztHMMePKuJKNc4SmwDVpNZPPa8aXd'

TEST_USER_SEED = 'b' * 32
TEST_USER_ID = 'did:iotics:iotAcP4c6Yp2TztCB6u2nRCrQcnRHwRJmbsD'
TEST_USER_ID_DELEG = '#testagent'


def make_private_key(seed, doc_type, count, expected_id=None, method=Identifier.SeedMethod.SEED_METHOD_NONE):
    mad = Identifier.seed_to_master(seed, method=method)
    pk_hex = Identifier.new_private_hex_from_path(mad, doc_type, count)
    prk = Identifier.private_hex_to_ECDSA(pk_hex)

    if expected_id is not None:
        pub = Identifier.private_ECDSA_to_public_ECDSA(prk)
        pub_hex = Identifier.public_ECDSA_to_bytes(pub).hex()
        actual_id = Identifier.make_identifier(pub_hex)
        if not Identifier.compare_identifier_only(actual_id, expected_id):
            raise ValueError(f'expected {expected_id} does not match {actual_id}')
    return prk


def setup_test_identity():
    """setup_test_identity: Make a bunch of test identities"""
    agent_pk = make_private_key(TEST_AGENT_SEED, Identifier.DIDType.AGENT, 0, TEST_AGENT_ID)
    agent_doc = Document.new_did_document(Identifier.DIDType.AGENT, agent_pk)
    tkn = Document.new_document_token(agent_doc, 'unit-test', agent_doc.id + agent_doc.public_keys[0].id, agent_pk)
    Resolver.register(tkn)

    user_pk = make_private_key(TEST_USER_SEED, Identifier.DIDType.USER, 0, TEST_USER_ID)
    user_doc = Document.new_did_document(Identifier.DIDType.USER, user_pk)

    proof = Document.new_proof(user_doc.id.encode('ascii'), agent_pk)
    deleg = Document.new_delegation(TEST_USER_ID_DELEG, TEST_AGENT_ID + agent_doc.public_keys[0].id, proof)
    user_doc.add_authentication_delegation(deleg)

    tkn = Document.new_document_token(user_doc, 'unit-test', user_doc.id + user_doc.public_keys[0].id, user_pk)
    Resolver.register(tkn)


if __name__ == '__main__':
    setup_test_identity()
