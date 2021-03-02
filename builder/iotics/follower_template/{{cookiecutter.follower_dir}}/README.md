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

    twin_list = list()

    try:
        # find twins
        twin_list = self.search_api.search_twins(text='Random')


...

    for twin in twin_list:
        subscription_id = None

        try:
            # follow twin's feed
            subscription_id = self.follow_api.subscribe_to_feed(
                self.follower_twin_id, twin.id.value, 'random_temperature_feed', self.follow_callback
            )
```


### Semantic based searches for and follows twins
This search will return the twins identified with the *Category Temperature* (ie it will return the twins 
including this Category in their meta data properties).
You can see the publisher adding such a category to the twins it creates in its `Creates a twin and sets its meta data` section.

It is possible to search for the twins identified with a set of properties (a "and" is performed).
Read more about properties in the Iotics documentation: [How to search](https://docs.iotics.com/docs/how-to-search).
```python
def follow_twins(self):
    """Find and follow twins"""

    twin_list = list()

    try:
        # Searching Semantically - run a search for all the twins identified with the Temperature category
        temperature_property = ModelProperty(key='http://data.iotics.com/ns/category',
                                             uri_value=Uri(value='http://data.iotics.com/category/Temperature'))
        twin_list = self.search_api.search_twins(properties=[temperature_property])# find twins


...

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

**Create yourself a user key and some credentials for this component**

```bash
# Create user seed, if you haven't already created a user seed e.g. in the publisher, in which case just use that seed
docker run --env RESOLVER="[address of resolver]" quay.io/iotic_labs/ioticsctl create seed
#> [user seed e.g. abcdef1234...]
docker run --env RESOLVER="[address of resolver]" quay.io/iotic_labs/ioticsctl create did --seed [user seed e.g. abcdef1234] --purpose user --number 0
#> DID Created: [user id e.g. did:iotics:xyz54321...]
docker run --env RESOLVER="[address of resolver]" quay.io/iotic_labs/ioticsctl wizard create --type agent --name follower-agent --seed [user seed e.g. abcdef1234] --purpose user --number 0
#> Created agent with ID [e.g. did:iotics:aaa111...] and delegated by user ID [e.g. did:iotics:xyz54321...]
#> SEED: [agent seed e.g. lmnop5678...]
```

**Run locally**

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
