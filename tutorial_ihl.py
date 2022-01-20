import base64
import json
import requests
from time import sleep

from iotics.host.api.data_types import BasicDataTypes
from iotics.host.api.qapi import QApiFactory
from iotic.web.rest.client.qapi import (
    GeoLocationUpdate,
    GeoLocation,
    LangLiteral,
    ModelProperty,
    StringLiteral,
    Uri,
    Value,
    Visibility,
)
from iotics.host.auth import AgentAuthBuilder
from iotics.host.conf.base import DataSourcesConfBase

MODEL_TYPE_PROPERTY = ModelProperty(
    key="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    uri_value=Uri(value="https://data.iotics.com/app#Model"),
)
ALLOW_ALL_HOSTS_PROPERTY = ModelProperty(
    key="http://data.iotics.com/public#hostAllowList",
    uri_value=Uri(value="http://data.iotics.com/public#allHosts"),
)
SOURCE_FEED_NAME = "currentTemp"
SOURCE_VALUE_LABEL = "temperature"
OUTPUT_FEED_NAME = "temperature_status"
OUTPUT_VALUE_LABEL = "status"
SUBSCRIPTIONS_MAP = {}
SENSORS_MAP = {}


def create_machine_from_model(data, agent_auth, api_factory):
    twin_api = api_factory.get_twin_api()
    feed_api = api_factory.get_feed_api()
    search_api = api_factory.get_search_api()

    model_twin = next(
        search_api.search_twins(
            text="Machine model (tutorial)", properties=[MODEL_TYPE_PROPERTY]
        )
    ).twins[0]
    model_twin_id = model_twin.id.value

    machines_dict = {}

    for machine_number, sensor_data in enumerate(data):
        machine_name = f"machine_{machine_number}"

        machine_twin_id = agent_auth.make_twin_id(machine_name)
        twin_api.create_twin(machine_twin_id)

        data_to_share = {SOURCE_VALUE_LABEL: sensor_data["temp"]}
        encoded_data = base64.b64encode(json.dumps(data_to_share).encode()).decode()

        for feed in model_twin.feeds:
            feed_id = feed.feed.id.value
            feed_info = feed_api.describe_feed(model_twin_id, feed_id).result
            feed_api.create_feed(machine_twin_id, feed_id)
            feed_api.update_feed(
                machine_twin_id,
                feed_id,
                add_labels=feed_info.labels,
                add_comments=feed_info.comments,
                add_values=feed_info.values,
                store_last=feed_info.store_last,
            )
            twin_api.update_twin(
                machine_twin_id,
                location=GeoLocationUpdate(location=GeoLocation(lat=51.5, lon=-0.1)),
                add_labels=[LangLiteral(lang="en", value=f"{machine_name} (tutorial)")],
                new_visibility=Visibility.PUBLIC,
                add_props=[
                    ALLOW_ALL_HOSTS_PROPERTY,
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
                clear_all_props=True,
            )
            feed_api.share_feed_data(
                twin_id=machine_twin_id,
                feed_id=feed_id,
                data=encoded_data,
                mime="application/json",
            )

        SENSORS_MAP[machine_name] = machine_twin_id
        print("Machine twin created:", machine_name)

    return machines_dict


def share_data(data, agent_auth, api_factory):
    feed_api = api_factory.get_feed_api()

    for machine_number, sensor_data in enumerate(data):
        machine_name = f"machine_{machine_number}"
        machine_twin_id = SENSORS_MAP.get(machine_name)
        if not machine_twin_id:
            continue
        data_to_share = {SOURCE_VALUE_LABEL: sensor_data["temp"]}
        encoded_data = base64.b64encode(json.dumps(data_to_share).encode()).decode()

        print("Sharing data for %s: %s" % (machine_name, data_to_share))
        feed_api.share_feed_data(
            twin_id=machine_twin_id,
            feed_id=SOURCE_FEED_NAME,
            data=encoded_data,
            mime="application/json",
        )


def follow_callback(sub_id, body):
    sensor = SUBSCRIPTIONS_MAP[sub_id]
    interaction_data = json.loads(
        base64.b64decode(body.payload.feed_data.data).decode("ascii")
    )

    if interaction_data[OUTPUT_VALUE_LABEL] == "extreme":
        print("%s: SENSOR IS OVERHEATING! OH THE HUMANITY!!" % sensor)


def follow_sensors(api_factory, interaction_twin_id):
    search_api = api_factory.get_search_api()
    follow_api = api_factory.get_follow_api()

    output_twins = []

    print("Searching for output twins", end="", flush=True)
    sleep(10)

    while len(output_twins) < len(SENSORS_MAP):
        output_twins = next(
            search_api.search_twins(
                # text="tutorial",
                properties=[
                    ModelProperty(
                        key="https://data.iotics.com/app#model",
                        uri_value=Uri(value=interaction_twin_id),
                    )
                ],
            )
        ).twins

        sleep(10)
        print(".", end="", flush=True)

    print("\nFound %s output twins" % len(output_twins))

    for sensor in output_twins:
        subscription_id = follow_api.subscribe_to_feed(
            sensor.id.value, sensor.id.value, OUTPUT_FEED_NAME, follow_callback
        )
        SUBSCRIPTIONS_MAP[subscription_id] = sensor.label


def create_interaction(agent_auth, api_factory, model_twin_id):
    twin_api = api_factory.get_twin_api()
    feed_api = api_factory.get_feed_api()

    interaction_twin_id = agent_auth.make_twin_id("SensorInteraction")
    twin_api.create_twin(interaction_twin_id)

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
                "feeds": [{"fieldIds": [SOURCE_VALUE_LABEL], "id": SOURCE_FEED_NAME}],
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

    twin_api.update_twin(
        interaction_twin_id,
        add_labels=[LangLiteral(lang="en", value="Sensor Overheating Alert")],
        add_props=[
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
        ],
        clear_all_props=True,
    )

    feed_api.create_feed(interaction_twin_id, OUTPUT_FEED_NAME)
    feed_value = Value(
        label=OUTPUT_VALUE_LABEL,
        comment="Temperature status: normal or extreme",
        data_type=BasicDataTypes.STRING.value,
    )
    feed_api.update_feed(
        interaction_twin_id,
        OUTPUT_FEED_NAME,
        add_labels=[LangLiteral(lang="en", value="Temperature status")],
        add_values=[feed_value],
        store_last=True,
    )

    print("Interaction twin created")

    return interaction_twin_id


def create_model(agent_auth, api_factory):
    twin_api = api_factory.get_twin_api()
    feed_api = api_factory.get_feed_api()

    model_twin_id = agent_auth.make_twin_id("MachineModel")

    twin_api.create_twin(model_twin_id)
    twin_api.update_twin(
        model_twin_id,
        add_labels=[LangLiteral(lang="en", value="Machine model (tutorial)")],
        new_visibility=Visibility.PUBLIC,
        add_props=[MODEL_TYPE_PROPERTY, ALLOW_ALL_HOSTS_PROPERTY],
        clear_all_props=True,
    )

    feed_api.create_feed(model_twin_id, SOURCE_FEED_NAME)
    feed_val = Value(
        label=SOURCE_VALUE_LABEL,
        comment="Temperature in degrees Celsius",
        unit="http://purl.obolibrary.org/obo/UO_0000027",
        data_type=BasicDataTypes.DECIMAL.value,
    )
    feed_api.update_feed(
        model_twin_id,
        SOURCE_FEED_NAME,
        add_labels=[LangLiteral(lang="en", value="Current temperature")],
        add_values=[feed_val],
        store_last=True,
    )

    print("Model twin created")

    return model_twin_id


def get_sensor_data():
    response = requests.get("http://flaskapi.dev.iotics.com/sensor_temp")
    if response.status_code > 400:
        print("Error %s from API: %s" % (response.status_code, response.reason))

    return response.json()


def main():
    agent_auth = AgentAuthBuilder.build_agent_auth(
        resolver_url="<resolver url>",
        user_seed="<from script output>",
        user_key_name="<from script output>",
        agent_seed="<from script output>",
        agent_key_name="<from script output>",
    )
    api_factory = QApiFactory(
        DataSourcesConfBase(
            qapi_url="<from index.json>", qapi_stomp_url="<from index.json>"
        ),
        agent_auth,
    )

    model_twin_id = create_model(agent_auth, api_factory)
    data = get_sensor_data()
    create_machine_from_model(data, agent_auth, api_factory)
    interaction_twin_id = create_interaction(agent_auth, api_factory, model_twin_id)
    follow_sensors(api_factory, interaction_twin_id)

    while True:
        print("\nGetting latest temperatures...")
        data = get_sensor_data()
        share_data(data, agent_auth, api_factory)

        sleep(5)


if __name__ == "__main__":
    main()
