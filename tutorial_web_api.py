import base64
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import requests
from iotics.lib.identity.api.high_level_api import get_rest_high_level_identity_api

RESOLVER_URL = "http://localhost:5000"  # <resolver url>
HOST = "http://localhost:8081"

AUTH_DELEGATION_NAME = "#AuthDeleg"
CONTROL_DELEGATION_NAME = "#ControlDeleg"

USER_KEY_NAME = "#MyUserKey"  # "<from script output>"
AGENT_KEY_NAME = "#MyAgentKey"  # "<from script output>"
USER_NAME = "#MyUserName"  # Optional
AGENT_NAME = "#MyAgentName"  # Optional

TWIN_KEY_NAME = "#MyTwin1Key"
TWIN_NAME = "#MyTwin1Name"

TOKEN_DURATION = 3600

MODEL_TYPE_PROPERTY = {
    "key": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    "uriValue": {"value": "https://data.iotics.com/app#Model"},
}
ALLOW_ALL_HOSTS_PROPERTY = {
    "key": "http://data.iotics.com/public#hostAllowList",
    "uriValue": {"value": "http://data.iotics.com/public#allHosts"},
}
SENSOR_TYPE_PROPERTY = {
    "key": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    "uriValue": {"value": "https://data.iotics.com/tutorial#Sensor"},
}
CREATED_FROM_MODEL_KEY = "https://data.iotics.com/app#model"
SERIAL_NUMBER_KEY = "https://data.iotics.com/tutorial#serialNumber"

FEED_ID = "currentTemp"
VALUE_LABEL = "temperature"

api = get_rest_high_level_identity_api(resolver_url=RESOLVER_URL)
agent_seed = api.create_seed()
client_app_id = f"randpub_{uuid4()}"


def get_new_token(agent_registered_id, user_registered_id):
    token = api.create_agent_auth_token(
        agent_registered_identity=agent_registered_id,
        user_did=user_registered_id.did,
        duration=TOKEN_DURATION,
    )

    return token


def create_headers(user_registered_id, agent_registered_id):
    token = get_new_token(agent_registered_id, user_registered_id)

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


def create_twin(twin_key_name, user_registered_id, agent_registered_id):
    twin_did = api.create_twin_with_control_delegation(
        twin_seed=agent_seed,
        twin_key_name=twin_key_name,
        agent_registered_identity=agent_registered_id,
        delegation_name=CONTROL_DELEGATION_NAME,
    )

    print("twin_did:", twin_did.did)

    payload = {"twinId": {"value": twin_did.did}}
    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    r = requests.post(
        f"{HOST}/qapi/twins",
        headers=headers,
        json=payload,
    )

    print("status_code:", r.status_code)

    return twin_did.did


def create_model(user_registered_id, agent_registered_id):
    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    # Create Model twin
    twin_did = create_twin(
        twin_key_name="#MachineModel",
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    # Add properties
    payload = {
        "labels": {"added": [{"lang": "en", "value": "Machine model (tutorial)"}]},
        "properties": {
            "added": [MODEL_TYPE_PROPERTY, ALLOW_ALL_HOSTS_PROPERTY],
            "clearedAll": True,
        },
        "newVisibility": {"visibility": "PUBLIC"},
    }

    r = requests.patch(
        f"{HOST}/qapi/twins/{twin_did}",
        headers=headers,
        data=json.dumps(payload),
    )

    print("ADD PROPERTIES status_code", r.status_code)

    # Add Feed
    feed_payload = {"feedId": {"value": FEED_ID}, "storeLast": True}

    r = requests.post(
        f"{HOST}/qapi/twins/{twin_did}/feeds",
        headers=headers,
        json=feed_payload,
    )
    print("ADD FEED status_code", r.status_code)

    # Add Value
    payload = {
        "storeLast": True,
        "labels": {"added": [{"lang": "en", "value": FEED_ID}]},
        "values": {
            "added": [
                {
                    "comment": "Temperature in degrees Celsius",
                    "dataType": "decimal",
                    "label": VALUE_LABEL,
                    "unit": "http://purl.obolibrary.org/obo/UO_0000027",
                }
            ]
        },
    }

    r = requests.patch(
        f"{HOST}/qapi/twins/{twin_did}/feeds/{FEED_ID}",
        headers=headers,
        json=payload,
    )
    print("ADD VALUE status_code", r.status_code)

    return twin_did


def get_sensor_data():
    response = requests.get("http://flaskapi.dev.iotics.com/sensor_temp")
    if response.status_code > 400:
        print("Error %s from API: %s" % (response.status_code, response.reason))

    return response.json()


def search_by_properties(user_registered_id, agent_registered_id):
    now = datetime.now(tz=timezone.utc)
    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )
    headers["Iotics-RequestTimeout"] = (now + timedelta(seconds=5)).isoformat()

    payload = {"filter": {"properties": [MODEL_TYPE_PROPERTY]}, "responseType": "FULL"}

    model_twin = {}

    with requests.post(
        f"{HOST}/qapi/searches",
        headers=headers,
        json=payload,
        stream=True,
        verify=False,
        params={"scope": "GLOBAL"},
    ) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_lines():
            response = json.loads(chunk)
            try:
                model_twin = response["result"]["payload"]["twins"][0]
            except KeyError:
                continue
            else:
                break

    print("model_twin:", model_twin)

    return model_twin


def create_machine_from_model(user_registered_id, agent_registered_id):
    model_twin = search_by_properties(user_registered_id, agent_registered_id)
    data = get_sensor_data()

    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    for machine_number, sensor_data in enumerate(data):
        machine_name = f"machine_{machine_number}"
        machine_twin_id = create_twin(
            machine_name, user_registered_id, agent_registered_id
        )

        # Add properties
        model_twin_did = model_twin["id"]["value"]
        payload = {
            "location": {"location": {"lat": 51.5, "lon": -0.1}},
            "labels": {
                "added": [{"lang": "en", "value": f"{machine_name} (tutorial)"}]
            },
            "properties": {
                "added": [
                    ALLOW_ALL_HOSTS_PROPERTY,
                    SENSOR_TYPE_PROPERTY,
                    {
                        "key": CREATED_FROM_MODEL_KEY,
                        "uriValue": {"value": model_twin_did},
                    },
                    {
                        "key": SERIAL_NUMBER_KEY,
                        "stringLiteralValue": {"value": "%06d" % machine_number},
                    },
                ],
                "clearedAll": True,
            },
            "newVisibility": {"visibility": "PUBLIC"},
        }

        r = requests.patch(
            f"{HOST}/qapi/twins/{machine_twin_id}",
            headers=headers,
            data=json.dumps(payload),
        )

        print("ADD PROPERTIES status_code", r.status_code)

        # Add Feeds
        for feed in model_twin["feeds"]:
            feed_id = feed["feed"]["id"]["value"]
            feed_store_last = feed["storeLast"]

            feed_payload = {"feedId": {"value": feed_id}, "storeLast": feed_store_last}

            r = requests.post(
                f"{HOST}/qapi/twins/{machine_twin_id}/feeds",
                headers=headers,
                json=feed_payload,
            )
            print("ADD FEED status_code", r.status_code)

            # Describe feed
            r = requests.get(
                f"{HOST}/qapi/twins/{model_twin_did}/feeds/{feed_id}",
                headers=headers,
            )

            feed_description = json.loads(r.text)
            print("feed_description:", feed_description)

            feed_label = feed_description["result"]["labels"][0]["value"]
            feed_lang = feed_description["result"]["labels"][0]["lang"]
            feed_values = feed_description["result"]["values"]

            # Add Value
            value_payload = {
                "storeLast": feed_store_last,
                "labels": {"added": [{"lang": feed_lang, "value": feed_label}]},
                "values": {"added": []},
            }

            for value in feed_values:
                value_comment = value["comment"]
                value_label = value["label"]
                value_unit = value["unit"]
                value_datatype = value["dataType"]

                val = {
                    "comment": value_comment,
                    "dataType": value_datatype,
                    "label": value_label,
                    "unit": value_unit,
                }
                value_payload["values"]["added"].append(val)

            r = requests.patch(
                f"{HOST}/qapi/twins/{machine_twin_id}/feeds/{feed_id}",
                headers=headers,
                json=value_payload,
            )
            print("ADD VALUE status_code", r.status_code)

        data_to_share = {VALUE_LABEL: sensor_data["temp"]}
        encoded_data = base64.b64encode(json.dumps(data_to_share).encode()).decode()
        data_to_share_payload = {
            "sample": {
                "data": encoded_data,
                "mime": "application/json",
                "occurredAt": datetime.now(tz=timezone.utc).isoformat(),
            }
        }

        r = requests.post(
            f"{HOST}/qapi/twins/{machine_twin_id}/feeds/{feed_id}/shares",
            headers=headers,
            json=data_to_share_payload,
        )
        print("SHARE SAMPLE DATA status_code", r.status_code)


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

    model_twin_did = create_model(user_registered_id, agent_registered_id)
    create_machine_from_model(user_registered_id, agent_registered_id)
    # interaction_twin_id = create_interaction(agent_auth, api_factory, model_twin_id)
    # follow_sensors(api_factory, interaction_twin_id)


if __name__ == "__main__":
    main()
