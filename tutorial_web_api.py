import base64
import json
from datetime import datetime
from uuid import uuid4

import requests
from iotics.lib.identity.api.high_level_api import get_rest_high_level_identity_api

RESOLVER_URL = "http://localhost:5000"  # <resolver url>
HOST = "https://api01.demo02.space.iotics.com"

AUTH_DELEGATION_NAME = "#AuthDeleg"
CONTROL_DELEGATION_NAME = "#ControlDeleg"

USER_KEY_NAME = "#MyUserKey"  # "<from script output>"
AGENT_KEY_NAME = "#MyAgentKey"  # "<from script output>"
USER_NAME = "#MyUserName"  # Optional
AGENT_NAME = "#MyAgentName"  # Optional

TWIN_KEY_NAME = "#MyTwin1Key"
TWIN_NAME = "#MyTwin1Name"

TOKEN_DURATION = 3600

api = get_rest_high_level_identity_api(resolver_url=RESOLVER_URL)
agent_seed = bytes.fromhex(api.create_seed())
client_app_id = f"randpub_{uuid4()}"


def create_headers(user_registered_id, agent_registered_id):
    token = api.create_agent_auth_token(
        agent_registered_identity=agent_registered_id,
        user_did=user_registered_id,
        duration=TOKEN_DURATION,
    )

    headers = {
        "accept": "application/json",
        "Iotics-ClientAppId": client_app_id,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    return headers


def create_user_and_agent_with_auth_delegation(
    user_key_name, agent_key_name, user_name=None, agent_name=None
):
    (
        user_registered_id,
        agent_registered_id,
    ) = api.create_user_and_agent_with_auth_delegation(
        user_seed=agent_seed,
        user_key_name=user_key_name,
        user_name=user_name,
        agent_seed=agent_seed,
        agent_key_name=agent_key_name,
        agent_name=agent_name,
        delegation_name=AUTH_DELEGATION_NAME,
    )

    return user_registered_id, agent_registered_id


def create_twin(twin_key_name, twin_name, user_registered_id, agent_registered_id):
    twin_id = api.create_twin_with_control_delegation(
        twin_seed=agent_seed,
        twin_key_name=twin_key_name,
        twin_name=twin_name,
        agent_registered_identity=agent_registered_id,
        delegation_name=CONTROL_DELEGATION_NAME,
    )

    payload = {"twinId": {"value": twin_id}}
    headers = create_headers(
        user_registered_id=user_registered_id, agent_registered_id=agent_registered_id
    )

    r = requests.post(
        f"{HOST}/qapi/twins",
        headers=headers,
        json=payload,
    )

    print("status_code:", r.status_code)

    return twin_id


def main():
    (
        user_registered_id,
        agent_registered_id,
    ) = create_user_and_agent_with_auth_delegation(
        user_key_name=USER_KEY_NAME,
        agent_key_name=AGENT_KEY_NAME,
        user_name=USER_NAME,
        agent_name=AGENT_NAME,
    )

    twin_id = create_twin(
        twin_key_name=TWIN_KEY_NAME,
        twin_name=TWIN_NAME,
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    # model_twin_id = create_model(agent_auth, api_factory)
    # data = get_sensor_data()
    # create_machine_from_model(data, agent_auth, api_factory)
    # interaction_twin_id = create_interaction(agent_auth, api_factory, model_twin_id)
    # follow_sensors(api_factory, interaction_twin_id)


if __name__ == "__main__":
    main()
