# {{cookiecutter.project_name}}

{% if cookiecutter.add_example_code == "YES" %}
The example code creates a twin and a feed on that twin and publishes a random temperature in Celsius to that feed, the publishing frequency is set by configuration.
{% else %}
TODO: summary
{% endif %}

## Context
{% if cookiecutter.add_example_code == "YES" %}
In `publisher.py` the example:

### Creates a twin and sets its meta data
```python
def _create_twin(self) -> str:
    # Create an twin id in the registerer
    twin_id, _, _ = self.agent_auth.make_twin_id(TWIN_NAME)

    # Create the twin
    api = self.qapi_factory.get_twin_api()
    api.create_twin(twin_id)
    return twin_id

def _set_twin_meta(self, twin_id: str):
    label = 'Random awesome twin'
    description = 'Awesome twin for random data'
    api = self.qapi_factory.get_twin_api()
    # Adding Semantic Meta data via property usage.
    # Here we are setting a "Category" property to this twin.
    # The twin is identified as a "Temperature" twin.
    category_property = ModelProperty(key='http://data.iotics.com/ns/category',
                                      uri_value=Uri(value='http://data.iotics.com/category/Temperature'))

    # Set twin location to London
    # This will make the twin visible in Iotics Cloud and it will enable the search by location.
    london_location = GeoLocationUpdate(location=GeoLocation(lat=51.507359, lon=-0.136439))
    api.update_twin(
        twin_id,
        add_tags=['random', 'awesome'],
        add_labels=[LangLiteral(value=label, lang='en')],
        add_comments=[LangLiteral(value=description, lang='en')],
        add_props=[category_property],
        location=london_location,
    )
```
#### Adding semantic meta data via property usage

In the code snippet above, a property is added to the twin meta data. This will allow semantic search based
on a set of properties. You can see the follower doing this type of search in 
its `Semantic searches for and follows twins` section.
Read more about properties in the Iotics documentation:
- [What is an IOTICS Digital Twin?](https://docs.iotics.com/docs/key-concepts#what-is-an-iotics-digital-twin)
- [Properties](https://docs.iotics.com/docs/setting-up-a-digital-twin#properties)

#### Getting started with Iotics Cloud
In the code snippet above, the London location is added to the twin meta data.
This will make the twin visible in Iotics Cloud.
Read more about Iotics Cloud in the Iotics documentation: [Getting started with Iotics Cloud](https://docs.iotics.com/docs/getting-started-with-iotics-cloud)


### Creates a feed and sets its meta data
```python
def _create_feed(self, twin_id: str) -> str:
    api = self.qapi_factory.get_feed_api()
    feed_name = 'random_temperature_feed'
    api.create_feed(twin_id, feed_name)
    return feed_name

def _set_feed_meta(self, twin_id: str, feed_name: str):
    label = 'Random temperature feed'
    description = f'Awesome feed generating a temperature in Celsius each {self.update_frequency_seconds} seconds'
    api = self.qapi_factory.get_feed_api()

    api.update_feed(
        twin_id, feed_name,
        add_labels=[LangLiteral(value=label, lang='en')],
        add_comments=[LangLiteral(value=description, lang='en')],
        # Whether this feed's most recent data can be retrieved via the InterestApi
        store_last=True,
        add_tags=['random', 'awesome'],
        add_values=[
            Value(label='temp',
                  data_type=BasicDataTypes.DECIMAL.value,
                  comment='a random temperature in Celsius',
                  unit='http://purl.obolibrary.org/obo/UO_0000027'),
        ]
    )
```

### Publishes data to the feed
```python
def _share_feed_data(self, twin_id: str, feed_name: str):
    non_encoded_data = {
        'temp': round(random.uniform(-10.0, 45.0), 2)
    }
    json_data = json.dumps(non_encoded_data)
    try:
        base64_encoded_data = base64.b64encode(json_data.encode()).decode()
    except TypeError as err:
        raise RandomTempPublisherBaseException(
            f'Can not encode data to share from {twin_id}/{feed_name}: {err}, {json_data}'
        ) from err

    api = self.qapi_factory.get_feed_api()
    api.share_feed_data(
        twin_id, feed_name,
        data=base64_encoded_data, mime='application/json',
        occurred_at=datetime.now(tz=timezone.utc).isoformat()
    )

    return non_encoded_data
```

In `conf.py`:

### Adds a configurable publishing frequency
```python
update_frequency_seconds: int = 10
```

> The configuration used in this template is built using pydantic (see https://pydantic-docs.helpmanual.io/)

As an example of how this configuration works, you can change this `update_frequency_seconds` value from its default of 10, by setting the environment variable `{{cookiecutter.conf_env_var_prefix}}UPDATE_FREQUENCY_SECONDS`
e.g. to set it to 1 second: `export {{cookiecutter.conf_env_var_prefix}}UPDATE_FREQUENCY_SECONDS=1`
{% else %}
TODO: summary
{% endif %}

## Tests and checks

> Note to run the following commands, you need to setup your own Python virtual environment:
```bash
python3 -mvenv env
source ./env/bin/activate
pip install -U pip setuptools
```

`make unit-static-tests` # Run unit and static tests using tox

`make static-tests` # Run static tests only, using tox

`make unit-tests` # Run unit tests only, using tox


## Running locally

**Create yourself a user key and some credentials for this component**

```bash
# Create user seed, if you haven't already created a user seed e.g. in the follower, in which case just use that seed
docker run --env RESOLVER="[address of resolver]" quay.io/iotic_labs/ioticsctl create seed
#> [user seed e.g. abcdef1234...]
docker run --env RESOLVER="[address of resolver]" quay.io/iotic_labs/ioticsctl create did --seed [user seed e.g. abcdef1234] --purpose user --number 0
#> DID Created: [user id e.g. did:iotics:xyz54321...]
docker run --env RESOLVER="[address of resolver]" quay.io/iotic_labs/ioticsctl wizard create --type agent --name publisher-agent --seed [user seed e.g. abcdef1234] --purpose user --number 0
#> Created agent with ID [e.g. did:iotics:aaa111...] and delegated by user ID [e.g. did:iotics:xyz54321...]
#> SEED: [agent seed e.g. lmnop5678...]
```


**Run locally**

```bash
cd ./{{cookiecutter.publisher_dir}}
# then export some environment variables
export SEED=[agent seed from above e.g. lmnop5678...]
export HOST_USER=[user did e.g. did:iotics:xyz54321...]
export QAPI_URL=[address of qapi]
export RESOLVER_HOST=[address of resolver for your space]

# next either
make docker-run-host # Run using the docker image
# OR
python3 -mvenv env
source ./env/bin/activate
pip install -U pip setuptools

make setup-dev

make run # Run using the sources from your computer
```
