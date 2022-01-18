import base64
import json
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import NamedTuple
from uuid import uuid4

import shortuuid
import stomp
from iotic.web.stomp.client import StompWSConnection12
from iotics.lib.identity.api.high_level_api import get_rest_high_level_identity_api
from requests import request

RESOLVER_URL = "<resolver_url>"
HOST = "<host_url>"

USER_KEY_NAME = "<from script output>"
AGENT_KEY_NAME = "<from script output>"
USER_SEED = bytes.fromhex("<from script output>")
AGENT_SEED = bytes.fromhex("<from script output>")

TWINS_VISIBILITY = "PRIVATE"

TWIN_TYPE_PREDICATE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
LABEL_PREDICATE = "http://www.w3.org/2000/01/rdf-schema#label"
COMMENT_PREDICATE = "http://www.w3.org/2000/01/rdf-schema#comment"
CREATED_FROM_MODEL_PREDICATE = "https://data.iotics.com/app#model"
MODEL_TYPE_PROPERTY = {
    "key": TWIN_TYPE_PREDICATE,
    "uriValue": {"value": "https://data.iotics.com/app#Model"},
}
ALLOW_ALL_HOSTS_PROPERTY = {
    "key": "http://data.iotics.com/public#hostAllowList",
    "uriValue": {"value": "http://data.iotics.com/public#allHosts"},
}

MODEL_LABEL = "Machine model (tutorial)"
FEED_ID = "currentTemp"
VALUE_LABEL = "temperature"
OUTPUT_FEED_NAME = "temperature_status"
OUTPUT_VALUE_LABEL = "status"

SUBSCRIPTIONS_MAP = {}


class RestApi(NamedTuple):
    method: str
    url: str


SENSOR_DATA = RestApi(method="GET", url="http://flaskapi.dev.iotics.com/sensor_temp")
INDEX_PAGE = RestApi(method="GET", url="{host}/index.json")

CREATE_TWIN = RestApi(method="POST", url="{host}/qapi/twins")
UPDATE_TWIN = RestApi(method="PATCH", url="{host}/qapi/twins/{twin_id}")
CREATE_FEED = RestApi(method="POST", url="{host}/qapi/twins/{twin_id}/feeds")
UPDATE_FEED = RestApi(method="PATCH", url="{host}/qapi/twins/{twin_id}/feeds/{feed_id}")
DESCRIBE_FEED = RestApi(method="GET", url="{host}/qapi/twins/{twin_id}/feeds/{feed_id}")
SHARE_DATA_FEED = RestApi(
    method="POST", url="{host}/qapi/twins/{twin_id}/feeds/{feed_id}/shares"
)
SUBSCRIBE_TO_FEED = RestApi(
    method="GET",
    url="/qapi/twins/{follower_twin_id}/interests/twins/{followed_twin_id}/feeds/{followed_feed_name}",
)
SEARCH_TWINS = RestApi(method="POST", url="{host}/qapi/searches")


class Tutorial:
    def __init__(self):
        self._api = get_rest_high_level_identity_api(resolver_url=RESOLVER_URL)
        self._client_app_id = f"web_api_{uuid4()}"
        self._client_ref = f"d-poc-{shortuuid.random(8)}"
        self._agent_registered_id = None
        self._user_registered_id = None
        self._headers = None
        self._sensors_map = {}

    def setup(self):
        (
            self._user_registered_id,
            self._agent_registered_id,
        ) = self._api.create_user_and_agent_with_auth_delegation(
            user_seed=USER_SEED,
            user_key_name=USER_KEY_NAME,
            agent_seed=AGENT_SEED,
            agent_key_name=AGENT_KEY_NAME,
            delegation_name="#AuthDeleg",
        )

        self._headers = {
            "accept": "application/json",
            "Iotics-ClientRef": self._client_ref,
            "Iotics-ClientAppId": self._client_app_id,
            "Content-Type": "application/json",
        }
        self._refresh_token()

    def _refresh_token(self):
        token = self._api.create_agent_auth_token(
            agent_registered_identity=self._agent_registered_id,
            user_did=self._user_registered_id.did,
            duration=3600,
        )

        self._headers["Authorization"] = f"Bearer {token}"

        return token

    def _make_api_call(self, method, url, json=None):
        response = request(method=method, url=url, headers=self._headers, json=json)

        response.raise_for_status()

        return response.json()

    def _create_twin(self, twin_key_name):
        twin_registered_id = self._api.create_twin_with_control_delegation(
            twin_seed=AGENT_SEED,
            twin_key_name=twin_key_name,
            agent_registered_identity=self._agent_registered_id,
            delegation_name="#ControlDeleg",
        )

        self._make_api_call(
            method=CREATE_TWIN.method,
            url=CREATE_TWIN.url.format(host=HOST),
            json={"twinId": {"value": twin_registered_id.did}},
        )

        return twin_registered_id.did

    def _update_twin_with_metadata(
        self, twin_id, visibility, properties=None, cleared_all=True, location=None
    ):
        payload = {"newVisibility": {"visibility": visibility}}

        if properties:
            payload["properties"] = {"added": properties, "clearedAll": cleared_all}
        if location:
            payload["location"] = location

        self._make_api_call(
            method=UPDATE_TWIN.method,
            url=UPDATE_TWIN.url.format(host=HOST, twin_id=twin_id),
            json=payload,
        )

    def _create_feed(self, twin_id, feed_id):
        self._make_api_call(
            method=CREATE_FEED.method,
            url=CREATE_FEED.url.format(host=HOST, twin_id=twin_id),
            json={"feedId": {"value": feed_id}},
        )

    def _describe_feed(self, twin_id, feed_id):
        feed_description = self._make_api_call(
            method=DESCRIBE_FEED.method,
            url=DESCRIBE_FEED.url.format(host=HOST, twin_id=twin_id, feed_id=feed_id),
        )

        return feed_description

    def _update_feed(
        self,
        twin_id,
        feed_id,
        metadata,
        properties=None,
        cleared_all=True,
        store_last=True,
    ):
        payload = {"storeLast": store_last, "values": {"added": metadata}}

        if properties:
            payload["properties"] = {"added": properties, "clearedAll": cleared_all}

        self._make_api_call(
            method=UPDATE_FEED.method,
            url=UPDATE_FEED.url.format(host=HOST, twin_id=twin_id, feed_id=feed_id),
            json=payload,
        )

    def _search_twins(self, properties=None, text=None, location=None, scope="LOCAL"):
        request_timeout = datetime.now(tz=timezone.utc) + timedelta(seconds=10)
        self._headers.update({"Iotics-RequestTimeout": request_timeout.isoformat()})

        payload = {"filter": {}, "responseType": "FULL"}

        if properties:
            payload["filter"]["properties"] = properties
        if text:
            payload["filter"]["text"] = text
        if location:
            payload["filter"]["location"] = location

        twins_list = []

        with request(
            method=SEARCH_TWINS.method,
            url=SEARCH_TWINS.url.format(host=HOST),
            headers=self._headers,
            json=payload,
            stream=True,
            verify=False,
            params={"scope": scope},
        ) as resp:
            resp.raise_for_status()

            for chunk in resp.iter_lines():
                response = json.loads(chunk)
                try:
                    twins_list = response["result"]["payload"]["twins"]
                except (KeyError, IndexError):
                    continue
                else:
                    break

        self._headers.pop("Iotics-RequestTimeout")
        return twins_list

    def _publish_feed_value(
        self, sensor_data, twin_id, feed_id, print_data=True, twin_label=None
    ):
        data_to_share = {VALUE_LABEL: sensor_data["temp"]}
        encoded_data = base64.b64encode(json.dumps(data_to_share).encode()).decode()
        data_to_share_payload = {
            "sample": {
                "data": encoded_data,
                "mime": "application/json",
                "occurredAt": datetime.now(tz=timezone.utc).isoformat(),
            }
        }

        self._make_api_call(
            method=SHARE_DATA_FEED.method,
            url=SHARE_DATA_FEED.url.format(host=HOST, twin_id=twin_id, feed_id=feed_id),
            json=data_to_share_payload,
        )

        if print_data:
            print(f"Sharing data for {twin_label}: {data_to_share}")

    def _subscribe_to_feed(
        self, follower_twin_id, followed_twin_id, followed_feed_name, callback
    ):
        response = self._make_api_call(
            method=INDEX_PAGE.method, url=INDEX_PAGE.url.format(host=HOST)
        )

        feed_path = f"/qapi/twins/{follower_twin_id}/interests/twins/{followed_twin_id}/feeds/{followed_feed_name}"

        stomp_handler = StompHandler(
            endpoint=response["stomp"], callback=callback, token=self._refresh_token()
        )
        stomp_handler.setup()
        stomp_handler.subscribe(
            destination=feed_path,
            subscription_id=self._headers["Iotics-ClientRef"],
            headers=self._headers,
        )

    @staticmethod
    def _follow_callback(headers, body):
        payload = json.loads(body)
        sub_id = headers["destination"].split("/")[3]
        data = payload["feedData"]["data"]

        try:
            sensor = SUBSCRIPTIONS_MAP[sub_id]
        except KeyError:
            print("No subscription found for twinId", sub_id)
        else:
            interaction_data = json.loads(base64.b64decode(data).decode("ascii"))

            if interaction_data[OUTPUT_VALUE_LABEL] == "extreme":
                print(f"{sensor}: SENSOR IS OVERHEATING! OH THE HUMANITY!!")

    def create_model(self):
        # Create Model twin
        model_twin_did = self._create_twin(twin_key_name="#MachineModel")

        # Add Properties
        self._update_twin_with_metadata(
            twin_id=model_twin_did,
            properties=[
                MODEL_TYPE_PROPERTY,
                ALLOW_ALL_HOSTS_PROPERTY,
                {
                    "key": LABEL_PREDICATE,
                    "langLiteralValue": {"value": MODEL_LABEL, "lang": "en"},
                },
            ],
            visibility=TWINS_VISIBILITY,
        )

        # Add Feed
        self._create_feed(twin_id=model_twin_did, feed_id=FEED_ID)

        # Add Value
        self._update_feed(
            twin_id=model_twin_did,
            feed_id=FEED_ID,
            properties=[
                {
                    "key": LABEL_PREDICATE,
                    "langLiteralValue": {"value": FEED_ID, "lang": "en"},
                }
            ],
            metadata=[
                {
                    "comment": "Temperature in degrees Celsius",
                    "dataType": "decimal",
                    "label": VALUE_LABEL,
                    "unit": "http://purl.obolibrary.org/obo/UO_0000027",
                }
            ],
        )

        print("Model twin created")

        return model_twin_did

    def create_machine_from_model(self):
        # Search for Machine Model
        twins_list = self._search_twins(
            properties=[MODEL_TYPE_PROPERTY], text=MODEL_LABEL
        )
        model_twin = twins_list[0]

        data = self.get_sensor_data()

        # Create new twins based on the model
        for machine_number, sensor_data in enumerate(data):
            machine_name = f"machine_{machine_number}"
            machine_twin_id = self._create_twin(twin_key_name=machine_name)

            # Add Properties
            model_twin_did = model_twin["id"]["value"]
            self._update_twin_with_metadata(
                twin_id=machine_twin_id,
                properties=[
                    ALLOW_ALL_HOSTS_PROPERTY,
                    {
                        "key": TWIN_TYPE_PREDICATE,
                        "uriValue": {
                            "value": "https://data.iotics.com/tutorial#Sensor"
                        },
                    },
                    {
                        "key": CREATED_FROM_MODEL_PREDICATE,
                        "uriValue": {"value": model_twin_did},
                    },
                    {
                        "key": "https://data.iotics.com/tutorial#serialNumber",
                        "stringLiteralValue": {"value": "%06d" % machine_number},
                    },
                    {
                        "key": LABEL_PREDICATE,
                        "langLiteralValue": {
                            "value": f"{machine_name} (tutorial)",
                            "lang": "en",
                        },
                    },
                ],
                location={"location": {"lat": 51.5, "lon": -0.1}},
                visibility=TWINS_VISIBILITY,
            )

            # Add Feeds
            for feed in model_twin["feeds"]:
                feed_id = feed["feed"]["id"]["value"]

                self._create_feed(twin_id=machine_twin_id, feed_id=feed_id)

                # Describe Model's feed
                feed_description = self._describe_feed(
                    twin_id=model_twin_did, feed_id=feed_id
                )

                feed_properties = feed_description["result"]["properties"]
                feed_values = feed_description["result"]["values"]
                store_last = feed_description["result"]["storeLast"]

                # Add Feed's Values
                values_metadata_list = []

                for value in feed_values:
                    value_comment = value["comment"]
                    value_label = value["label"]
                    value_unit = value["unit"]
                    value_datatype = value["dataType"]

                    metadata = {
                        "comment": value_comment,
                        "dataType": value_datatype,
                        "label": value_label,
                        "unit": value_unit,
                    }
                    values_metadata_list.append(metadata)

                self._update_feed(
                    twin_id=machine_twin_id,
                    feed_id=feed_id,
                    properties=feed_properties,
                    metadata=values_metadata_list,
                    store_last=store_last,
                )

                # Share first sample of data
                self._publish_feed_value(
                    sensor_data=sensor_data,
                    twin_id=machine_twin_id,
                    feed_id=feed_id,
                    print_data=False,
                )

            self._sensors_map[machine_name] = machine_twin_id
            print("Machine twin created:", machine_name)

    def create_interaction(self, model_twin_did):
        # Create Interaction twin
        twin_did = self._create_twin(twin_key_name="#SensorInteraction")

        print("Interaction Twin created")

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

        # Add Properties
        self._update_twin_with_metadata(
            twin_id=twin_did,
            visibility=TWINS_VISIBILITY,
            properties=[
                MODEL_TYPE_PROPERTY,
                ALLOW_ALL_HOSTS_PROPERTY,
                {
                    "key": TWIN_TYPE_PREDICATE,
                    "uriValue": {"value": "https://data.iotics.com/app#Interaction"},
                },
                {
                    "key": "https://data.iotics.com/app#interactionConfig",
                    "stringLiteralValue": {"value": json.dumps(interaction_config)},
                },
                {
                    "key": LABEL_PREDICATE,
                    "langLiteralValue": {
                        "value": "Sensor Overheating Alert",
                        "lang": "en",
                    },
                },
            ],
        )

        # Add Feed
        self._create_feed(twin_id=twin_did, feed_id=OUTPUT_FEED_NAME)

        # Add Feed's Value
        self._update_feed(
            twin_id=twin_did,
            feed_id=OUTPUT_FEED_NAME,
            properties=[
                {
                    "key": LABEL_PREDICATE,
                    "langLiteralValue": {"value": "Temperature status", "lang": "en"},
                }
            ],
            metadata=[
                {
                    "comment": "Temperature status: normal or extreme",
                    "dataType": "string",
                    "label": OUTPUT_VALUE_LABEL,
                }
            ],
        )

        return twin_did

    def share_data(self, data):
        for machine_number, sensor_data in enumerate(data):
            machine_name = f"machine_{machine_number}"
            machine_twin_id = self._sensors_map.get(machine_name)
            if not machine_twin_id:
                continue

            self._publish_feed_value(
                sensor_data=sensor_data,
                twin_id=machine_twin_id,
                feed_id=FEED_ID,
                twin_label=machine_name,
            )

    def follow_sensors(self, interaction_twin_id):
        output_twins = []

        print("Searching for output twins", end="", flush=True)

        while len(output_twins) < len(self._sensors_map):
            output_twins = self._search_twins(
                properties=[
                    {
                        "key": CREATED_FROM_MODEL_PREDICATE,
                        "uriValue": {"value": interaction_twin_id},
                    }
                ],
            )
            sleep(10)
            print(".", end="", flush=True)

        print("\nFound %s output twins" % len(output_twins))

        for sensor in output_twins:
            sensor_id = sensor["id"]["value"]
            self._subscribe_to_feed(
                sensor_id, sensor_id, OUTPUT_FEED_NAME, self._follow_callback
            )

            sensor_label = None

            # Search for the label property
            for prop in sensor["properties"]:
                if prop["key"] == LABEL_PREDICATE:
                    sensor_label = prop["langLiteralValue"]["value"]
                    break

            if sensor_label:
                SUBSCRIPTIONS_MAP[sensor_id] = sensor_label

    def get_sensor_data(self):
        sensor_data = self._make_api_call(
            method=SENSOR_DATA.method, url=SENSOR_DATA.url
        )

        return sensor_data


class StompHandler:
    def __init__(self, endpoint, callback, token):
        self._endpoint = endpoint
        self._token = token
        self._stomp_client = None
        self._callback = callback

    def setup(self):
        self._stomp_client = StompWSConnection12(endpoint=self._endpoint)
        self._stomp_client.set_listener(
            "stomp_listener", StompListener(self._stomp_client, self._callback)
        )

        self._stomp_client.connect(wait=True, passcode=self._token)

    def subscribe(self, destination, subscription_id, headers):
        self._stomp_client.subscribe(
            destination=destination, id=subscription_id, headers=headers
        )

    def disconnect(self):
        self._stomp_client.disconnect()


class StompListener(stomp.ConnectionListener):
    def __init__(self, stomp_client, callback):
        self._stomp_client = stomp_client
        self._callback = callback

    def on_error(self, headers, body):
        print('received an error "%s"' % body)

    def on_message(self, headers, body):
        self._callback(headers, body)

    def on_disconnected(self):
        self._stomp_client.disconnect()
        print("disconnected")


def main():
    tutorial = Tutorial()
    tutorial.setup()

    model_twin_id = tutorial.create_model()
    tutorial.create_machine_from_model()
    interaction_twin_id = tutorial.create_interaction(model_twin_id)
    tutorial.follow_sensors(interaction_twin_id)

    while True:
        print("\nGetting latest temperatures...")
        data = tutorial.get_sensor_data()
        tutorial.share_data(data)

        sleep(5)


if __name__ == "__main__":
    main()
