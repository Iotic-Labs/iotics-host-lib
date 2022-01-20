import base64
import json
from time import sleep

import requests
from iotic.web.rest.client.qapi import (
    GeoLocation,
    LangLiteral,
    ModelProperty,
    StringLiteral,
    UpsertFeedWithMeta,
    Uri,
    Value,
    Visibility,
)
from iotics.host.api.data_types import BasicDataTypes
from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder
from iotics.host.conf.base import DataSourcesConfBase

RESOLVER_URL = "resolver_url"
QAPI_URL = "qapi_url"
QAPI_STOMP_URL = "qapi_stomp_url"

USER_KEY_NAME = "user_key_name"
AGENT_KEY_NAME = "agent_key_name"
USER_SEED = "user_seed"
AGENT_SEED = "agent_seed"

MODEL_TYPE_PROPERTY = ModelProperty(
    key="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    uri_value=Uri(value="https://data.iotics.com/app#Model"),
)
ALLOW_ALL_HOSTS_PROPERTY = ModelProperty(
    key="http://data.iotics.com/public#hostAllowList",
    uri_value=Uri(value="http://data.iotics.com/public#allHosts"),
)
LABEL_PREDICATE = "http://www.w3.org/2000/01/rdf-schema#label"

MODEL_LABEL = "Machine model (tutorial)"
SOURCE_FEED_NAME = "currentTemp"
SOURCE_VALUE_LABEL = "temperature"
OUTPUT_FEED_NAME = "temperature_status"
OUTPUT_VALUE_LABEL = "status"
SUBSCRIPTIONS_MAP = {}
SENSORS_MAP = {}

TWIN_VISIBILITY = Visibility.PRIVATE


class Tutorial:
    def __init__(self):
        self._agent_auth = None
        self._twin_api = None
        self._search_api = None
        self._feed_api = None
        self._follow_api = None

    def setup(self):
        self._agent_auth = AgentAuthBuilder.build_agent_auth(
            resolver_url=RESOLVER_URL,
            user_seed=USER_SEED,
            user_key_name=USER_KEY_NAME,
            agent_seed=AGENT_SEED,
            agent_key_name=AGENT_KEY_NAME,
        )

        api_factory = QApiFactory(
            DataSourcesConfBase(qapi_url=QAPI_URL, qapi_stomp_url=QAPI_STOMP_URL),
            self._agent_auth,
        )
        self._twin_api = api_factory.get_twin_api()
        self._search_api = api_factory.get_search_api()
        self._feed_api = api_factory.get_feed_api()
        self._follow_api = api_factory.get_follow_api()

    def create_model(self):
        # Create Model Twin
        model_twin_id = self._agent_auth.make_twin_id("MachineModel")

        # Update Twin with Metadata, Feed and Value
        self._twin_api.upsert_twin(
            twin_id=model_twin_id,
            visibility=TWIN_VISIBILITY,
            properties=[
                MODEL_TYPE_PROPERTY,
                ALLOW_ALL_HOSTS_PROPERTY,
                ModelProperty(
                    key=LABEL_PREDICATE,
                    lang_literal_value=LangLiteral(value=MODEL_LABEL, lang="en"),
                ),
            ],
            feeds=[
                UpsertFeedWithMeta(
                    id=SOURCE_FEED_NAME,
                    store_last=True,
                    properties=[
                        ModelProperty(
                            key=LABEL_PREDICATE,
                            lang_literal_value=LangLiteral(
                                value="Current temperature", lang="en"
                            ),
                        )
                    ],
                    values=[
                        Value(
                            label=SOURCE_VALUE_LABEL,
                            comment="Temperature in degrees Celsius",
                            unit="http://purl.obolibrary.org/obo/UO_0000027",
                            data_type=BasicDataTypes.DECIMAL.value,
                        )
                    ],
                )
            ],
        )

        print("Model twin created")

        return model_twin_id

    def create_machine_from_model(self, data):
        # Search for Machine Model
        twins_list = self._search_api.search_twins(
            properties=[MODEL_TYPE_PROPERTY], text=MODEL_LABEL
        )

        model_twin = next(twins_list).twins[0]
        model_twin_id = model_twin.id.value

        # Create new twins based on the model
        for machine_number, sensor_data in enumerate(data):
            machine_name = f"machine_{machine_number}"
            machine_twin_id = self._agent_auth.make_twin_id(machine_name)

            # Create Twin
            self._twin_api.create_twin(machine_twin_id)

            # Get the Model Twin's feeds list
            model_feeds_list = model_twin.feeds
            # Get the id of the first (and only) feed in the list
            feed_id = next(iter(model_feeds_list)).feed.id.value
            # Describe the feed to get metadata and properties
            feed_info = self._feed_api.describe_feed(
                twin_id=model_twin_id, feed_id=feed_id
            ).result

            # Update Twin with Metadata, Feed(s) and Value(s)
            self._twin_api.upsert_twin(
                twin_id=machine_twin_id,
                visibility=TWIN_VISIBILITY,
                location=GeoLocation(lat=51.5, lon=-0.1),
                properties=[
                    ALLOW_ALL_HOSTS_PROPERTY,
                    ModelProperty(
                        key=LABEL_PREDICATE,
                        lang_literal_value=LangLiteral(
                            value=f"{machine_name} (tutorial)", lang="en"
                        ),
                    ),
                    ModelProperty(
                        key="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                        uri_value=Uri(value="https://data.iotics.com/tutorial#Sensor"),
                    ),
                    ModelProperty(
                        key="https://data.iotics.com/app#model",
                        uri_value=Uri(value=str(model_twin_id)),
                    ),
                    ModelProperty(
                        key="https://data.iotics.com/tutorial#serialNumber",
                        string_literal_value=StringLiteral(
                            value="%06d" % machine_number
                        ),
                    ),
                ],
                feeds=[
                    UpsertFeedWithMeta(
                        id=feed_id,
                        store_last=feed_info.store_last,
                        properties=feed_info.properties,
                        values=feed_info.values,
                    )
                ],
            )

            # Share first sample of data
            self._publish_feed_value(
                sensor_data, twin_id=machine_twin_id, feed_id=feed_id, print_data=False
            )

            SENSORS_MAP[machine_name] = machine_twin_id

            print("Machine twin created:", machine_name)

    def create_interaction(self, model_twin_id):
        # Create Interaction Twin
        interaction_twin_id = self._agent_auth.make_twin_id("SensorInteraction")

        # Setup Interaction config
        interaction_config = {
            "enabled": True,
            "rules": [
                {
                    "transformation": {
                        "conditions": [
                            {
                                "fieldsIncludedInOutput": [SOURCE_VALUE_LABEL],
                                "jsonLogic": {">": [{"var": SOURCE_VALUE_LABEL}, 30]},
                            }
                        ],
                        "outputFeedId": OUTPUT_FEED_NAME,
                        "outputFieldId": OUTPUT_VALUE_LABEL,
                        "outputTrueValue": "extreme",
                        "outputFalseValue": "normal",
                        "sourceFeedId": SOURCE_FEED_NAME,
                        "sourceId": "1",
                    }
                }
            ],
            "sources": [
                {
                    "cleanupRateS": 900,
                    "feeds": [
                        {"fieldIds": [SOURCE_VALUE_LABEL], "id": SOURCE_FEED_NAME}
                    ],
                    "filter": {
                        "properties": [
                            {
                                "key": "https://data.iotics.com/app#model",
                                "value": {"uriValue": {"value": model_twin_id}},
                            }
                        ],
                        "text": None,
                    },
                    "id": "1",
                    "modelDid": model_twin_id,
                    "refreshRateS": 300,
                }
            ],
        }

        # Update Twin with Metadata, Feed and Value
        self._twin_api.upsert_twin(
            twin_id=interaction_twin_id,
            visibility=TWIN_VISIBILITY,
            properties=[
                MODEL_TYPE_PROPERTY,
                ALLOW_ALL_HOSTS_PROPERTY,
                ModelProperty(
                    key="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                    uri_value=Uri(value="https://data.iotics.com/app#Interaction"),
                ),
                ModelProperty(
                    key="https://data.iotics.com/app#interactionConfig",
                    string_literal_value=StringLiteral(
                        value=json.dumps(interaction_config)
                    ),
                ),
                ModelProperty(
                    key=LABEL_PREDICATE,
                    lang_literal_value=LangLiteral(
                        value="Sensor Overheating Alert", lang="en"
                    ),
                ),
            ],
            feeds=[
                UpsertFeedWithMeta(
                    id=OUTPUT_FEED_NAME,
                    store_last=True,
                    properties=[
                        ModelProperty(
                            key=LABEL_PREDICATE,
                            lang_literal_value=LangLiteral(
                                value="Temperature status", lang="en"
                            ),
                        )
                    ],
                    values=[
                        Value(
                            label=OUTPUT_VALUE_LABEL,
                            comment="Temperature status: normal or extreme",
                            data_type=BasicDataTypes.STRING.value,
                        )
                    ],
                )
            ],
        )

        print("Interaction twin created")

        return interaction_twin_id

    def follow_sensors(self, interaction_twin_id):
        output_twins = []

        print("Searching for output twins", end="", flush=True)
        sleep(10)

        while len(output_twins) < len(SENSORS_MAP):
            output_twins = next(
                self._search_api.search_twins(
                    properties=[
                        ModelProperty(
                            key="https://data.iotics.com/app#model",
                            uri_value=Uri(value=interaction_twin_id),
                        )
                    ]
                )
            ).twins

            sleep(10)
            print(".", end="", flush=True)

        print(f"\nFound {len(output_twins)} output twins")

        for sensor in output_twins:
            subscription_id = self._follow_api.subscribe_to_feed(
                follower_twin_id=sensor.id.value,
                followed_twin_id=sensor.id.value,
                followed_feed_name=OUTPUT_FEED_NAME,
                callback=self._follow_callback,
            )
            sensor_label = self._find_label(properties=sensor.properties)

            if sensor_label:
                SUBSCRIPTIONS_MAP[subscription_id] = sensor_label

    def get_sensor_data(self):
        response = requests.get("http://flaskapi.dev.iotics.com/sensor_temp")
        if response.status_code > 400:
            print(f"Error {response.status_code} from API: {response.reason}")

        return response.json()

    def share_data(self, data):
        for machine_number, sensor_data in enumerate(data):
            machine_name = f"machine_{machine_number}"
            machine_twin_id = SENSORS_MAP.get(machine_name)
            if not machine_twin_id:
                continue

            self._publish_feed_value(
                sensor_data,
                twin_id=machine_twin_id,
                feed_id=SOURCE_FEED_NAME,
                twin_label=machine_name,
            )

    def _publish_feed_value(
        self, sensor_data, twin_id, feed_id, print_data=True, twin_label=None
    ):
        data_to_share = {SOURCE_VALUE_LABEL: sensor_data["temp"]}
        encoded_data = base64.b64encode(json.dumps(data_to_share).encode()).decode()

        self._feed_api.share_feed_data(
            twin_id, feed_id, data=encoded_data, mime="application/json"
        )

        if print_data:
            print(f"Sharing data for {twin_label}: {data_to_share}")

    def _follow_callback(self, sub_id, body):
        sensor = SUBSCRIPTIONS_MAP[sub_id]
        interaction_data = json.loads(
            base64.b64decode(body.payload.feed_data.data).decode("ascii")
        )

        if interaction_data[OUTPUT_VALUE_LABEL] == "extreme":
            print(f"{sensor}: SENSOR IS OVERHEATING! OH THE HUMANITY!!")

    def _find_label(self, properties):
        for prop in properties:
            if prop.key == LABEL_PREDICATE:
                return prop.lang_literal_value.value

        return None


def main():
    tutorial = Tutorial()
    tutorial.setup()

    model_twin_id = tutorial.create_model()
    data = tutorial.get_sensor_data()
    tutorial.create_machine_from_model(data)
    interaction_twin_id = tutorial.create_interaction(model_twin_id)
    tutorial.follow_sensors(interaction_twin_id)

    while True:
        print("\nGetting latest temperatures...")
        data = tutorial.get_sensor_data()
        tutorial.share_data(data)

        sleep(5)


if __name__ == "__main__":
    main()
