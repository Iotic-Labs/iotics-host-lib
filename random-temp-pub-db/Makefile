ROOT_DIR=$(shell git rev-parse --show-toplevel)
V = 0
Q = $(if $(filter 1,$V),,@)
M = $(shell printf "\033[34;1m▶\033[0m")

APP_NAME = iotics-data-randpub
VERSION ?= dev

.PHONY: build run

setup-dev:
	$Q VERSION=dev pip install --no-cache-dir \
		-f ../deps \
		-e .[dev,lint,test]

### Unit and static checks

unit-static-tests: setup-dev # Run unit and static tests locally
	$Q VERSION=dev tox -vv

unit-tests: setup-dev # Run only unit tests locally
	$Q VERSION=dev tox -vv -e py3 -- $(TEST_ARGS)

static-checks: setup-dev # Run only static tests locally
	$Q VERSION=dev tox -vv -e flake8,pylint


### Docker

docker-build: ## Build the container
	$Q cd $(ROOT_DIR) \
	   && docker build --build-arg VERSION=$(VERSION) -t $(APP_NAME) -f random-temp-pub-db/Dockerfile .


USER_SEED ?= "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
USER_KEY_NAME ?= "00"  # along with seed used to create DID
# USER_NAME  # stored in did document, if unset default used like #user-0
AGENT_SEED ?= "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
AGENT_KEY_NAME ?= "00"  # along with seed used to create DID
# AGENT_NAME  # stored in did document, if unset default used like #agent-0

QAPI_URL ?= http://localhost:8081/qapi
RESOLVER_HOST ?= http://localhost:5000
VERIFY_SSL ?= False
LOG_LEVEL ?= INFO

docker-run: docker-build  ## Docker run of the publisher against a running host (see README)
	$Q docker run --rm --network host \
		-e RANDPUB_QAPI_URL=$(QAPI_URL)	\
		-e RANDPUB_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
        -e RANDPUB_AUTH__USER_SEED=$(USER_SEED) \
        -e RANDPUB_AUTH__USER_KEY_NAME=$(USER_KEY_NAME) \
        -e RANDPUB_AUTH__USER_NAME=$(USER_NAME) \
        -e RANDPUB_AUTH__AGENT_SEED=$(AGENT_SEED) \
        -e RANDPUB_AUTH__AGENT_KEY_NAME=$(AGENT_KEY_NAME) \
        -e RANDPUB_AUTH__AGENT_NAME=$(AGENT_NAME) \
		-e RANDPUB_ROOT_LOG_LEVEL=$(LOG_LEVEL) \
		-e RANDPUB_VERFIY_SSL=$(VERIFY_SSL) \
		$(APP_NAME)
run:
	$Q RANDPUB_ROOT_LOG_LEVEL=$(LOG_LEVEL) \
	   RANDPUB_QAPI_URL=$(QAPI_URL) \
	   RANDPUB_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
	   RANDPUB_AUTH__USER_SEED=$(USER_SEED) \
	   RANDPUB_AUTH__USER_KEY_NAME=$(USER_KEY_NAME) \
	   RANDPUB_AUTH__USER_NAME=$(USER_NAME) \
	   RANDPUB_AUTH__AGENT_SEED=$(AGENT_SEED) \
	   RANDPUB_AUTH__AGENT_KEY_NAME=$(AGENT_KEY_NAME) \
	   RANDPUB_AUTH__AGENT_NAME=$(AGENT_NAME) \
	   RANDPUB_VERIFY_SSL=$(VERIFY_SSL) \
	   run-rand-pub
