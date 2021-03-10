ROOT_DIR=$(shell git rev-parse --show-toplevel)
V = 0
Q = $(if $(filter 1,$V),,@)
M = $(shell printf "\033[34;1m▶\033[0m")

APP_NAME = iotics-data-weathertemplate
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
	   && docker build --build-arg VERSION=$(VERSION) -t $(APP_NAME) -f weather-template/Dockerfile .


SEED ?= "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
HOST_USER ?= "did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM"
QAPI_URL ?= http://localhost:8081/qapi
QAPI_STOMP_URL ?= ws://localhost:8080/ws
RESOLVER_HOST ?= http://localhost:5000
VERIFY_SSL ?= False

docker-run-host: docker-build  ## Docker run of the follower against a running host (see README)
	$Q docker run --rm --network host \
		-e WEATHERTEMPL_QAPI_URL=$(QAPI_URL)	\
		-e WEATHERTEMPL_QAPI_STOMP_URL=$(QAPI_STOMP_URL)	\
		-e WEATHERTEMPL_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
        -e WEATHERTEMPL_AUTH__SEED=$(SEED) \
        -e WEATHERTEMPL_AUTH__USER=$(HOST_USER) \
		-e WEATHERTEMPL_ROOT_LOG_LEVEL=DEBUG \
		-e WEATHERTEMPL_VERFIY_SSL=$(VERIFY_SSL) \
		$(APP_NAME)
run:
	$Q WEATHERTEMPL_ROOT_LOG_LEVEL=INFO \
	   WEATHERTEMPL_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
	   WEATHERTEMPL_QAPI_URL=$(QAPI_URL)	\
	   WEATHERTEMPL_QAPI_STOMP_URL=$(QAPI_STOMP_URL)	\
	   WEATHERTEMPL_AUTH__SEED=$(SEED) \
	   WEATHERTEMPL_AUTH__USER=$(HOST_USER) \
	   WEATHERTEMPL_VERIFY_SSL=$(VERIFY_SSL) \
	   run-weather-templ
