# FaaS POC


TODO: summary


## Context

TODO: summary



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
cd ./faas
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
