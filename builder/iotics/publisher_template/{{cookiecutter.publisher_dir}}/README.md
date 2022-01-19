# {{cookiecutter.project_name}}

{% if cookiecutter.add_example_code == "YES" %}
The example code creates a twin and a feed on that twin and publishes a random temperature in Celsius to that feed, the publishing frequency is set by configuration.
{% else %}
TODO: summary
{% endif %}

## Context
{% if cookiecutter.add_example_code == "YES" %}
In `publisher.py` the example:

### Creating a twin and setting its basic metadata
The update_twin method has parameters for setting some basic metadata to make the twin accessible via text- and
location-based searches. Further capabilities for describing twins are shown [below](#adding-more-semantic-metadata-via-custom-properties).
```python
def _create_twin(self) -> str:
    # Create an twin id in the registrar
    twin_id = self.agent_auth.make_twin_id(TWIN_NAME)

    # Create the twin
    self.twin_api.create_twin(twin_id)
    return twin_id

def _set_twin_meta(self, twin_id: str):
    # The RDF Schema provides "label" and "comment" properties to provide basic details of resources: https://www.w3.org/TR/rdf-schema/#ch_label
    twin_label = ModelProperty(
        key='http://www.w3.org/2000/01/rdf-schema#label',
        lang_literal_value=LangLiteral(lang='en', value='Twin 1')
    )
    twin_description = ModelProperty(
        key='http://www.w3.org/2000/01/rdf-schema#comment',
        lang_literal_value=LangLiteral(lang='en', value='The first twin we made in Iotics')
    )

    # Set twin location to London, using the GeoLocationUpdate class to provide its latitude and longitude.
    # This will make the twin visible in Iotics Cloud and it will enable the search by location.
    london_location = GeoLocationUpdate(location=GeoLocation(lat=51.507359, lon=-0.136439))

    # More information on the parameters of this method is available in the iotics-host-lib source code.
    self.twin_api.update_twin(
        twin_id,
        add_props=[twin_label, twin_description],  # List or tuple of ModelProperty instances
        location=london_location, # Must be instance of GeoLocation, as constructed above.
    )
```

#### Getting started with Iotics Cloud
In the code snippet above, the London location is added to the twin metadata.
This will make the twin visible in Iotics Cloud.
Read more about Iotics Cloud in the Iotics documentation: [Getting started with Iotics Cloud](https://docs.iotics.com/docs/getting-started-with-iotics-cloud)

### Creating a feed and setting its metadata
Feeds are described using many of the same properties as twins (eg labels and comments), as shown above. Additionally,
Feeds have associated Values with details of what sort of data is present in each shared update. For example, the Feed
below has one Value, explaining that each share will have a decimal number (not a string or boolean, for instance)
representing degrees Celsius. The `unit` parameter is set to an IRI representing °C in a popular ontology for units of
measure.
```python
def _create_feed(self, twin_id: str) -> str:
    feed_name = 'random_temperature_feed'
    self.feed_api.create_feed(twin_id, feed_name)
    return feed_name

def _set_feed_meta(self, twin_id: str, feed_name: str):
    feed_label = ModelProperty(
        key='http://www.w3.org/2000/01/rdf-schema#label',
        lang_literal_value=LangLiteral(lang='en', value='Random temperature feed')
    )
    feed_description = ModelProperty(
        key='http://www.w3.org/2000/01/rdf-schema#comment',
        lang_literal_value=LangLiteral(
            lang='en',
            value=f'Awesome feed generating a temperature in Celsius each {self.update_frequency_seconds} seconds'
        )
    )

    self.feed_api.update_feed(
        add_props=[feed_label, feed_description],
        store_last=True,  # Whether this feed's most recent data can be retrieved via the InterestApi
        add_values=[
            Value(label='temp',
                  data_type=BasicDataTypes.DECIMAL.value,
                  comment='a random temperature in Celsius',
                  unit='http://purl.obolibrary.org/obo/UO_0000027'),
        ]
    )
```

### Creating a twin and its feeds, and their metadata all at once
The above twin and its feed could be created and updated in one call using the `upsert_twin` method, as shown below. 
This method will set a given twin's state to precisely the one specified by its arguments, deleting all other feeds 
and metadata if present.

```python
def _create_twin_and_feed(self, twin_name: str, feed_name: str):
    twin_id = self.agent_auth.make_twin_id(twin_name)
    london_location = GeoLocation(lat=51.507359, lon=-0.136439)  # No GeoLocationUpdate wrapper

    # definition of properties omitted; they are the same as above.
    # twin_label = ModelProperty(...

    self.twin_api.upsert_twin(
        twin_id,
        properties=[twin_label, twin_description],
        location=london_location,
        feeds=[UpsertFeedWithMeta(
            id=feed_name,
            store_last=True,
            properties=[feed_label, feed_description],
            values=[Value(
                label='temp',
                data_type=BasicDataTypes.DECIMAL.value,
                comment='a random temperature in Celsius',
                unit='http://purl.obolibrary.org/obo/UO_0000027'
            )]
        )]
    )
```
### Publishes data to the feed
The data shared to a Feed should be a base64-encoded dict keyed with the Feed's Value labels. You may also explicitly
set a time associated with this share.
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

    self.feed_api.share_feed_data(
        twin_id, feed_name,
        data=base64_encoded_data, mime='application/json',
        occurred_at=datetime.now(tz=timezone.utc).isoformat()
    )

    return non_encoded_data
```


#### Adding more semantic metadata via custom properties
All metadata describing twins is stored using the Resource Description Framework ([RDF](https://www.w3.org/TR/rdf11-concepts/)),
which makes statements about the world using subject-predicate-object triples. For purposes of this walkthrough, think
of predicates and objects as keys and values describing the subject (usually a Twin or Feed).

In the code snippet below, a custom property is added to the twin while setting the metadata. Custom properties allow
the user to set the value of the predicate (the `key` parameter), an IRI referencing the definition of the property
(ie, what sort of thing it describes and how). The object is set using a second parameter, either one of various
`literal` types or a `uri` -- see the ModelProperty source code.

Twins so decorated may be found in a semantic search based on a set of properties. You can see the follower doing this
type of search in its `Semantic searches for and follows twins` section.
Read more about properties in the Iotics documentation:
- [What is an IOTICS Digital Twin?](https://docs.iotics.com/docs/key-concepts#what-is-an-iotics-digital-twin)
- [Properties](https://docs.iotics.com/docs/setting-up-a-digital-twin#properties)

```python
def _set_twin_meta(self, twin_id: str):
    category_property = ModelProperty(key='http://data.iotics.com/ns/category',
                                      uri_value=Uri(value='http://data.iotics.com/category/Temperature'))
    
    # Using upsert_twin will cause any other properties, metadata and/or feeds to be cleared! To avoid this, use 
    # update_twin below.
    # self.twin_api.upsert_twin(twin_id, properties=[category_property])

    self.twin_api.update_twin(
        twin_id,
        add_props=[category_property]
    )
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

## Tests and checks - Environment setup

### Linux
The basic linux terminal can be used for execution.

### Windows - MinGW32/MinGW64 setup
If the user is building the connector on windows, the MinGW terminal needs to be configured. This terminal will be installed along with Git. To open this terminal use git bash.

To check if make is configured in MinGW, open git bash and run `make` command
```bash
make -v
```
If make is not installed/configured, follow the steps to configure make in MinGW:
1. Download mingw installer from [__mingw-get-setup__](https://sourceforge.net/projects/mingw/)
2. Complete the setup and then run the Mingw installer from location you have installed `mingw-get-setup` (Shortcut should be on desktop by default).
3. In the installer select `All packages` in the left pane and then select/mark `mingw32-mingw-get` with class `bin`  `gui` and `lic`. 
4. Once marked click on `Installation` tab and select `Apply Changes` and click `Apply` in the dialogue box that pops up. This will install `mingw-get` package which can be used to install make.
5. To apply the package to the git bash mingw terminal, copy the content in the target directory of Mingw Installer(usually Folder named `MinGW` in `C:\` drive) to MinGW(MinGw64/32) folder in target folder where Git is installed.
6.  Once done restart git bash and run following command to install make:
    ```bash
    mingw-get install mingw32-make
    ```
7.  This will install make and test the installation by running
    ```bash
    make -v
    ```


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


### Create yourself credentials for this component
Set the resolver host
```bash
export RESOLVER_HOST=https://your.resolver
```
Run `gen_creds.py` script from the `iotics-host-lib` directory to generate:
- **USER_SEED** and **USER_KEY_NAME** together used to generate your agent DID
- **AGENT_SEED** and **AGENT_KEY_NAME** together used to generate your agent DID

More info about DIDs can be found on [docs.iotics.com](docs.iotics.com).

```bash
# Create a virtual environment:
python3 -mvenv venv
source venv/bin/activate
pip install -U pip setuptools
pip install iotics-identity
# or use an existing environment and then call:
./scripts/gen_creds.py --resolver [resolver url e.g. https://your.resolver]
```
Once the script successfully completes, take a note of variables for your component:
```bash
export RESOLVER_HOST=https://your.resolver
export USER_SEED=dec8615d1fc1598ceade592a6d756cad3846d8a2fc9a26af7251df7eb152b771
export USER_KEY_NAME=00
export AGENT_SEED=000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
export AGENT_KEY_NAME=00
```
Those should be kept safe and be present in the environment in which you are running your connector.
If you are using the same user for a publisher component and a follower component, you can reuse the same
USER SEED, but **note that this should NOT be stored in production environment with your component,
instead keep it safe and secure elsewhere**.


### Run component
The environment variables can be set either by updating the values within the make file generated by cookiecutter or by exporting as follows in the terminal.
```bash
cd ./{{cookiecutter.publisher_dir}}
# then export some environment variables
export RESOLVER_HOST=[address of resolver for your space]
export USER_SEED=[user seed from above e.g. lmnop5678...]
export USER_KEY_NAME=[user seed from above e.g. 00]
export AGENT_SEED=[agent seed from above e.g. lmnop5678...]
export AGENT_KEY_NAME=[user seed from above e.g. 00]
export QAPI_URL=[address of qapi]

# next either
make docker-run # Run using the docker image
# OR
python3 -mvenv env
source ./env/bin/activate
pip install -U pip setuptools

make setup-dev

make run # Run using the sources from your computer
```


### Monitoring and alerting
To be able to analyse Iotics Host Library usage Prometheus metrics, ensure you have a Python client installed in your
Connector's environment: 
```bash
pip install prometheus_client
```

Next add to e.g. `publisher.py:run_publisher` the following:
```python
import prometheus_client
prometheus_client.start_http_server(8001)
```

Now you should be able to see metrics per the "Monitoring and alerting" section in the Iotics Host Library readme.
