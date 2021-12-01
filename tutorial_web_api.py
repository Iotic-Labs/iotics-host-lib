import base64
import json
from datetime import datetime, timedelta, timezone
from time import sleep
from uuid import uuid4

import requests
import shortuuid
from iotics.lib.identity.api.high_level_api import get_rest_high_level_identity_api
from iotic.web.stomp.client import StompWSConnection12
from stomp.listener import PrintingListener

# Localhost
# RESOLVER_URL = "http://localhost:5000"
# HOST = "http://localhost:8081"
# api = get_rest_high_level_identity_api(resolver_url=RESOLVER_URL)
# USER_KEY_NAME = "#MyUserKey"
# AGENT_KEY_NAME = "#MyAgentKey"
# USER_SEED = bytes.fromhex(
#     "a7631ed56882044021224d06c8deb966afb6a5db2115c805900b02c35b8188ce"
# )
# AGENT_SEED = bytes.fromhex(
#     "0319fa3c553fe101ce2ce7876944af450609f9a823235dd4f25d8b5743d66a4a"
# )

# Sapples space
RESOLVER_URL = "https://did.stg.iotics.com"
HOST = "https://sapples-dev.dev.iotics.space"
api = get_rest_high_level_identity_api(resolver_url=RESOLVER_URL)
USER_KEY_NAME = "00"
AGENT_KEY_NAME = "00"
USER_SEED = bytes.fromhex(
    "a7631ed56882044021224d06c8deb966afb6a5db2115c805900b02c35b8188ce"
)
AGENT_SEED = bytes.fromhex(
    "1da9c9a589bb2763380a97124c474e316cba5ba0d98163790a5e31c59549f617"
)

AUTH_DELEGATION_NAME = "#AuthDeleg"
CONTROL_DELEGATION_NAME = "#ControlDeleg"

TOKEN_DURATION = 3600

TWIN_TYPE_PREDICATE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
CREATED_FROM_MODEL_PREDICATE = "https://data.iotics.com/app#model"
SERIAL_NUMBER_PREDICATE = "https://data.iotics.com/tutorial#serialNumber"
HOST_ALLOW_LIST_PREDICATE = "http://data.iotics.com/public#hostAllowList"
INTERACTION_CONFIG_PREDICATE = "https://data.iotics.com/app#interactionConfig"

INTERACTION_OBJECT = "https://data.iotics.com/app#Interaction"
MODEL_OBJECT = "https://data.iotics.com/app#Model"
ALL_HOSTS_OBJECT = "http://data.iotics.com/public#allHosts"
TUTORIAL_SENSOR_OBJECT = "https://data.iotics.com/tutorial#Sensor"

MODEL_TYPE_PROPERTY = {
    "key": TWIN_TYPE_PREDICATE,
    "uriValue": {"value": MODEL_OBJECT},
}
ALLOW_ALL_HOSTS_PROPERTY = {
    "key": HOST_ALLOW_LIST_PREDICATE,
    "uriValue": {"value": ALL_HOSTS_OBJECT},
}
SENSOR_TYPE_PROPERTY = {
    "key": TWIN_TYPE_PREDICATE,
    "uriValue": {"value": TUTORIAL_SENSOR_OBJECT},
}

FEED_ID = "currentTemp"
VALUE_LABEL = "temperature"

OUTPUT_FEED_NAME = "temperature_status"
OUTPUT_VALUE_LABEL = "status"

SUBSCRIPTIONS_MAP = {}
SENSORS_MAP = {}


client_app_id = f"randpub_{uuid4()}"
client_ref = f"d-poc-{shortuuid.random(8)}"

# logger = logging.getLogger(__name__)


# class FollowStompListener(ConnectionListener):
#     def __init__(self, message_handler, disconnect_handler):
#         self._message_handler = message_handler
#         self._disconnect_handler = disconnect_handler
#         self.regenerate_token = False
#         self.receipts = set()
#         self.errors = {}

#     def clear(self):
#         self.receipts = set()
#         self.errors = {}

#     def on_connected(self, headers: dict, body):
#         logger.info("Stomp Follow connected %s, %s", headers, body)

#     def on_disconnected(self):
#         logger.warning("Stomp Follow disconnected")
#         if self._disconnect_handler:
#             logger.debug("Attempting reconnect in 1s")
#             sleep(1)
#             try:
#                 self._disconnect_handler()
#             except Exception as ex:
#                 raise DataSourcesStompNotConnected(ex) from ex

#     @staticmethod
#     def to_interest_fetch_response(headers: dict, body):
#         payload = deserialize(body, FetchInterestResponsePayload)  # TODO
#         headers = Headers(
#             client_app_id=headers.get("Iotics-ClientAppId"),
#             client_ref=headers.get("Iotics-ClientRef"),
#             consumer_group=headers.get("Iotics-ConsumerGroup"),
#             request_timeout=headers.get("Iotics-RequestTimeout"),
#             transaction_ref=headers.get("Iotics-TransactionRef", "").split(","),
#         )
#         return FetchInterestResponse(headers=headers, payload=payload)

#     def on_message(self, headers: dict, body):
#         destination = headers["destination"]

#         logger.debug("[On message] Destination: - %s", destination)

#         try:
#             deserialised_resp = self.to_interest_fetch_response(headers, body)
#         except Exception as ex:  # pylint: disable=broad-except
#             self.errors[headers["receipt-id"]] = "Deserialization error: %s" % ex
#         else:
#             self._message_handler(headers, deserialised_resp)

#     def on_error(self, headers: dict, body):
#         logger.error("Received stomp error body: %s headers: %s", body, headers)
#         try:
#             # This will be improved once https://ioticlabs.atlassian.net/browse/FO-1889 will be done
#             error = get_stomp_error_message(body) or "No error body"
#             if error in (
#                 "UNAUTHENTICATED: token expired",
#                 "The connection frame does not contain valid credentials.",
#             ):
#                 self.regenerate_token = True
#         except Exception as ex:  # pylint: disable=broad-except
#             error = "Deserialization error: %s" % ex
#         self.errors[headers["receipt-id"]] = error

#     def on_receipt(self, headers: dict, body):
#         self.receipts.add(headers["receipt-id"])


# class StompClient:
#     def __init__(
#         self,
#         stomp_url,
#         token,
#         client_app_id,
#         verify_ssl=False,
#         reconnect_attempts_max=10,
#         heartbeats=(10000, 10000),
#     ):
#         parametrized_connect = partial(
#             self._connect, reconnect_attempts_max, heartbeats
#         )
#         self.active = True
#         self.client = None
#         self.client_app_id = client_app_id
#         self.listener = FollowStompListener(self._message_handler, parametrized_connect)
#         self.stomp_url = stomp_url
#         self._subscriptions = {}
#         self.token = token
#         self.verify_ssl = verify_ssl
#         try:
#             parametrized_connect()
#         except Exception as ex:
#             raise DataSourcesStompNotConnected(ex) from ex


def get_stomp_client():
    resp = requests.get(f"{HOST}/index.json").json()
    stomp_endpoint = resp["stomp"]
    stomp_client = StompWSConnection12(endpoint=stomp_endpoint)
    stomp_client.set_ssl(verify=False)
    stomp_client.set_listener("log_listener", PrintingListener())
    stomp_client.connect(wait=True, passcode=get_new_token())

    return stomp_client


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
        "Iotics-ClientRef": client_ref,
        "Iotics-ClientAppId": client_app_id,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    return headers


def create_user_and_agent_with_auth_delegation(user_key_name, agent_key_name):
    (
        user_registered_id,
        agent_registered_id,
    ) = api.create_user_and_agent_with_auth_delegation(
        user_seed=USER_SEED,
        user_key_name=user_key_name,
        agent_seed=AGENT_SEED,
        agent_key_name=agent_key_name,
        delegation_name=AUTH_DELEGATION_NAME,
    )

    return user_registered_id, agent_registered_id


def create_twin(twin_key_name, user_registered_id, agent_registered_id):
    twin_registered_id = api.create_twin_with_control_delegation(
        twin_seed=AGENT_SEED,
        twin_key_name=twin_key_name,
        agent_registered_identity=agent_registered_id,
        delegation_name=CONTROL_DELEGATION_NAME,
    )

    print("twin_registered_id.did:", twin_registered_id.did)

    payload = {"twinId": {"value": twin_registered_id.did}}
    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    r = requests.post(
        f"{HOST}/qapi/twins",
        headers=headers,
        json=payload,
    )

    print("CREATE TWIN text:", r.text)

    return twin_registered_id.did


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
        "labels": {"added": [{"lang": "en", "value": "Machine model (test)"}]},
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

    payload = {
        "filter": {"properties": [MODEL_TYPE_PROPERTY], "text": "test"},
        "responseType": "FULL",
    }

    model_twin = {}

    with requests.post(
        f"{HOST}/qapi/searches",
        headers=headers,
        json=payload,
        stream=True,
        verify=False,
        params={"scope": "LOCAL"},
    ) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_lines():
            response = json.loads(chunk)
            try:
                model_twin = response["result"]["payload"]["twins"][0]
            except (KeyError, IndexError):
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
            "labels": {"added": [{"lang": "en", "value": f"{machine_name} (test)"}]},
            "properties": {
                "added": [
                    ALLOW_ALL_HOSTS_PROPERTY,
                    SENSOR_TYPE_PROPERTY,
                    {
                        "key": CREATED_FROM_MODEL_PREDICATE,
                        "uriValue": {"value": model_twin_did},
                    },
                    {
                        "key": SERIAL_NUMBER_PREDICATE,
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

        SENSORS_MAP[machine_name] = machine_twin_id
        print("Machine twin created:", machine_name)


def create_interaction(user_registered_id, agent_registered_id, model_twin_did):
    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    # Create Interaction twin
    twin_did = create_twin(
        twin_key_name="#SensorInteraction",
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    print("INTERACTION TWIN created")

    interaction_config = {
        "enabled": True,
        "rules": [
            {
                "transformation": {
                    "conditions": [
                        {
                            "fieldsIncludedInOutput": [VALUE_LABEL],
                            "jsonLogic": {">": [{"var": VALUE_LABEL}, 30]},
                        }
                    ],
                    "outputFeedId": OUTPUT_FEED_NAME,
                    "outputFieldId": OUTPUT_VALUE_LABEL,
                    "outputTrueValue": "extreme",
                    "outputFalseValue": "normal",
                    "sourceFeedId": FEED_ID,
                    "sourceId": "1",
                }
            }
        ],
        "sources": [
            {
                "cleanupRateS": 900,
                "feeds": [{"fieldIds": [VALUE_LABEL], "id": FEED_ID}],
                "filter": {
                    "properties": [
                        {
                            "key": "https://data.iotics.com/app#model",
                            "value": {"uriValue": {"value": model_twin_did}},
                        }
                    ],
                    "text": None,
                },
                "id": "1",
                "modelDid": model_twin_did,
                "refreshRateS": 300,
            }
        ],
    }

    # Add properties
    payload = {
        "labels": {"added": [{"lang": "en", "value": "Sensor Overheating Alert1"}]},
        "properties": {
            "added": [
                MODEL_TYPE_PROPERTY,
                ALLOW_ALL_HOSTS_PROPERTY,
                {
                    "key": TWIN_TYPE_PREDICATE,
                    "uriValue": {"value": INTERACTION_OBJECT},
                },
                {
                    "key": INTERACTION_CONFIG_PREDICATE,
                    "stringLiteralValue": {"value": json.dumps(interaction_config)},
                },
            ],
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
    feed_payload = {"feedId": {"value": OUTPUT_FEED_NAME}, "storeLast": True}

    r = requests.post(
        f"{HOST}/qapi/twins/{twin_did}/feeds",
        headers=headers,
        json=feed_payload,
    )
    print("ADD FEED status_code", r.status_code)

    # Add Value
    payload = {
        "storeLast": True,
        "labels": {"added": [{"lang": "en", "value": "Temperature status"}]},
        "values": {
            "added": [
                {
                    "comment": "Temperature status: normal or extreme",
                    "dataType": "string",
                    "label": OUTPUT_VALUE_LABEL,
                }
            ]
        },
    }

    r = requests.patch(
        f"{HOST}/qapi/twins/{twin_did}/feeds/{OUTPUT_FEED_NAME}",
        headers=headers,
        json=payload,
    )
    print("ADD VALUE status_code", r.status_code)

    return twin_did


def subscribe_to_feed(
    user_registered_id,
    agent_registered_id,
    follower_twin_id,
    followed_twin_id,
    followed_feed_name,
    # callback,
):
    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    feed_path = f"/qapi/twins/{follower_twin_id}/interests/twins/{followed_twin_id}/feeds/{followed_feed_name}"

    stomp_client = get_stomp_client()
    stomp_client.subscribe(
        destination=feed_path, id=headers["Iotics-ClientRef"], headers=headers
    )

    # r = requests.get(
    #     f"{HOST}/qapi/twins/{follower_twin_id}/interests/twins/{followed_twin_id}"
    #     f"/feeds/{followed_feed_name}/samples/last",
    #     headers=headers,
    # )

    result = json.loads(r.text)

    print("subscribe_to_feed:", result)


def follow_sensors(user_registered_id, agent_registered_id, interaction_twin_id):
    output_twins = []

    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    while len(output_twins) < len(SENSORS_MAP):
        headers["Iotics-RequestTimeout"] = (
            datetime.now(tz=timezone.utc) + timedelta(seconds=10)
        ).isoformat()

        payload = {
            "filter": {
                "text": "test",
                "properties": [
                    {
                        "key": CREATED_FROM_MODEL_PREDICATE,
                        "uriValue": {"value": interaction_twin_id},
                    }
                ],
            },
            "responseType": "FULL",
        }

        with requests.post(
            f"{HOST}/qapi/searches",
            headers=headers,
            json=payload,
            stream=True,
            verify=False,
            params={"scope": "LOCAL"},
        ) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_lines():
                response = json.loads(chunk)
                try:
                    output_twins = response["result"]["payload"]["twins"]
                except KeyError:
                    continue
                else:
                    break

        print("output_twins:", output_twins)
        sleep(10)
        # print(".", end="", flush=True)

    print("\nFound %s output twins" % len(output_twins))

    for sensor in output_twins:
        sensor_id = sensor["id"]["value"]
        subscribe_to_feed(
            user_registered_id,
            agent_registered_id,
            sensor_id,
            sensor_id,
            OUTPUT_FEED_NAME,
        )
        # SUBSCRIPTIONS_MAP[subscription_id] = sensor.label


def share_data(data, user_registered_id, agent_registered_id):
    headers = create_headers(
        user_registered_id=user_registered_id,
        agent_registered_id=agent_registered_id,
    )

    for machine_number, sensor_data in enumerate(data):
        machine_name = f"machine_{machine_number}"
        machine_twin_id = SENSORS_MAP.get(machine_name)
        if not machine_twin_id:
            continue
        data_to_share = {VALUE_LABEL: sensor_data["temp"]}
        encoded_data = base64.b64encode(json.dumps(data_to_share).encode()).decode()
        data_to_share_payload = {
            "sample": {
                "data": encoded_data,
                "mime": "application/json",
                "occurredAt": datetime.now(tz=timezone.utc).isoformat(),
            }
        }

        print("Sharing data for %s: %s" % (machine_name, data_to_share))

        r = requests.post(
            f"{HOST}/qapi/twins/{machine_twin_id}/feeds/{FEED_ID}/shares",
            headers=headers,
            json=data_to_share_payload,
        )
        print("SHARE SAMPLE DATA status_code", r.status_code)


def follow_callback(sub_id, body):
    sensor = SUBSCRIPTIONS_MAP[sub_id]
    interaction_data = json.loads(
        base64.b64decode(body.payload.feed_data.data).decode("ascii")
    )

    if interaction_data[OUTPUT_VALUE_LABEL] == "extreme":
        print("%s: SENSOR IS OVERHEATING! OH THE HUMANITY!!" % sensor)


def main():
    (
        user_registered_id,
        agent_registered_id,
    ) = create_user_and_agent_with_auth_delegation(
        user_key_name=USER_KEY_NAME,
        agent_key_name=AGENT_KEY_NAME,
    )

    model_twin_did = create_model(user_registered_id, agent_registered_id)
    create_machine_from_model(user_registered_id, agent_registered_id)
    interaction_twin_id = create_interaction(
        user_registered_id, agent_registered_id, model_twin_did
    )
    follow_sensors(user_registered_id, agent_registered_id, interaction_twin_id)

    # while True:
    #     print("\nGetting latest temperatures...")
    #     data = get_sensor_data()
    #     share_data(data, user_registered_id, agent_registered_id)

    #     sleep(5)


if __name__ == "__main__":
    main()
