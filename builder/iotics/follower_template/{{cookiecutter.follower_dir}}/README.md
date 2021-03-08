# {{cookiecutter.project_name}}

{% if cookiecutter.add_example_code == "YES" %}
The example code searches for the twin that contains text 'Random' and follows its feed.
{% else %}
TODO: summary
{% endif %}

## Context
{% if cookiecutter.add_example_code == "YES" %}
In `follower.py` the example:

### Creates a twin representing the follower
```python
    def create_follower_twin(self):
        twin_id, _, _ = self.agent_auth.make_twin_id('{{cookiecutter.follower_class_name}}')
        self.twin_api.create_twin(twin_id)
        self.follower_twin_id = twin_id
```

### Text based searches for and follows twins
This search will return twins with matching text in their or their feeds' labels, descriptions or tags. You can see the publisher adding such a tag to the twins it creates in its `_set_twin_meta` method.
```python
def follow_twins(self):
    """Find and follow twins"""

    search_resp_gen = None

    try:
        # search for twins
        # note: a generator is returned because responses are yielded
        # as they come in asynchronously from the network of hosts
        search_resp_gen = self.search_api.search_twins(text='Random')


...

    for search_resp in search_resp_gen:
        for twin in search_resp.twins:
            subscription_id = None

            try:
                # follow twin's feed
                subscription_id = self.follow_api.subscribe_to_feed(
                    self.follower_twin_id, twin.id.value, 'random_temperature_feed', self.follow_callback
                )
```


### Semantic based searches for and follows twins
The generated example searches for twins using a text based search, you can however search using semantics.
The search in the example code snippet below, will return the twins identified with the *Temperature Category*
(ie it will return the twins including this Category in their meta data properties).
You can see how to add semantic meta data in the `Adding semantic meta data via property usage` section
in the README of the publisher.

Note: it is possible to search for the twins identified with a set of properties (a "and" is performed).
Read more about search in the Iotics documentation: [How to search](https://docs.iotics.com/docs/how-to-search).
```python
from iotic.web.rest.client.qapi import ModelProperty, Uri
[...]
def follow_twins(self):
    """Find and follow twins"""

...
    try:
        # Searching Semantically - run a search for all the twins identified with the Temperature category
        temperature_property = ModelProperty(key='http://data.iotics.com/ns/category',
                                             uri_value=Uri(value='http://data.iotics.com/category/Temperature'))
        search_resp_gen = self.search_api.search_twins(properties=[temperature_property])


...

    for search_resp in search_resp_gen:
        for twin in twin_list:
            subscription_id = None

            try:
                # follow twin's feed
                subscription_id = self.follow_api.subscribe_to_feed(
                    self.follower_twin_id, twin.id.value, 'random_temperature_feed', self.follow_callback
                )
```

### Logs the received data
```python
def follow_callback(header, body):  # pylint: disable=W0613
    decoded_data = base64.b64decode(body.payload.feed_data.data).decode('ascii')
    temperature = json.loads(decoded_data)
    timestamp = body.payload.feed_data.occurred_at.isoformat()

    logger.info('Received temperature data %s at time %s', temperature, timestamp)
```

### Repeatedly searches to find and follow new twins
```python
def run(self):
    logger.info('Follower started')
    self.create_follower_twin()

    while True:
        self.follow_twins()
        logger.info('Sleeping for %s seconds', self.loop_time)
        sleep(self.loop_time)
```

### Get feed's most recent data via the InterestApi
> Get most recent data is available via the InterestApi if the followed feed has the tag `store_last` set to `True`
> (cf. publisher example)
```python
def get_most_recent_data(self, followed_twin_id: str, feed_id: str):
    """ Get feed's most recent data via the InterestApi
        Note: the feed meta data must include store_last=True
    """
    logger.info('Get most recent data via InterestApi')
    most_recent_data = self.interest_api.get_feed_last_stored(follower_twin_id=self.follower_twin_id,
                                                              followed_twin_id=followed_twin_id,
                                                              feed_id=feed_id)
    decoded_data = base64.b64decode(most_recent_data.feed_data.data).decode()
    temperature = json.loads(decoded_data)
    logger.info('Most recent data %s', temperature)
```

In `conf.py`:

### Adds a configurable search frequency
```python
update_frequency_seconds: int = 300
```

> The configuration is used in this template is built using pydantic (see https://pydantic-docs.helpmanual.io/)

As an example of how this configuration works, you can change this `update_frequency_seconds` value from its default of 300, by setting the environment variable `{{cookiecutter.conf_env_var_prefix}}UPDATE_FREQUENCY_SECONDS`
e.g. to set it to 10 seconds: `export {{cookiecutter.conf_env_var_prefix}}UPDATE_FREQUENCY_SECONDS=10`
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


### Create yourself credentials for this component
Run `gen_creds.py` script from the `iotics-host-lib` directory to generate:
- **USER SEED** used to generate and retrieve your user DID,
- **USER DID** required by all your connectors to run and connect to Iotics host,
- **AGENT SEED** a unique seed required for each of your connector.

More info about DIDs can be found on [docs.iotics.com](docs.iotics.com).

```bash
# Create a virtual environment:
python3 -mvenv venv
source venv/bin/activate
pip install -U pip setuptools
pip install -f deps iotic.lib.identity
# or use an existing one and then call:
./scripts/gen_creds.py
```
Once the script successfully completes, take a note of variables for your component:
```bash
export RESOLVER_HOST=https://your.resolver
export HOST_USER=did:iotics:iot1234567890aBcDeFgHiJkLmNoPQrStUvW
export SEED=000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
```
Those should be kept safe and be present in the environment in which you are running your connector.  
If you are using the same user for a publisher component and a follower component, you can reuse the same
USER SEED, but **note that this should NOT be stored in production environment with your component,
instead keep it safe and secure elsewhere**. The seed can be stored and recognised by the `gen_creds.py`.


### Run component
```bash
cd ./{{cookiecutter.follower_dir}}
# then export some environment variables
export SEED=[agent seed from above e.g. lmnop5678...]
export HOST_USER=[user did e.g. did:iotics:xyz54321...]
export QAPI_URL=[address of qapi]
export QAPI_STOMP_URL=[address of qapi]
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
