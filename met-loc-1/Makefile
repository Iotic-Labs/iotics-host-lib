ROOT_DIR=$(shell git rev-parse --show-toplevel)
V = 0
Q = $(if $(filter 1,$V),,@)
M = $(shell printf "\033[34;1m▶\033[0m")

APP_NAME = iotics-data-metloc1
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
	   && docker build --build-arg VERSION=$(VERSION) -t $(APP_NAME) -f met-loc-1/Dockerfile .


SEED ?= "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
HOST_USER ?= "did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM"
QAPI_URL ?= http://localhost:8081/qapi
RESOLVER_HOST ?= http://localhost:5000
VERIFY_SSL ?= False

docker-run-host: docker-build  ## Docker run of the publisher against a running host (see README)
	$Q docker run --rm --network host \
		-e METLOC1_QAPI_URL=$(QAPI_URL)	\
		-e METLOC1_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
        -e METLOC1_AUTH__SEED=$(SEED) \
        -e METLOC1_AUTH__USER=$(HOST_USER) \
		-e METLOC1_ROOT_LOG_LEVEL=DEBUG \
		-e METLOC1_VERFIY_SSL=$(VERIFY_SSL) \
		$(APP_NAME)
run:
	$Q METLOC1_ROOT_LOG_LEVEL=INFO \
	   METLOC1_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
	   METLOC1_QAPI_URL=$(QAPI_URL) \
	   METLOC1_AUTH__SEED=$(SEED) \
	   METLOC1_AUTH__USER=$(HOST_USER) \
	   METLOC1_VERIFY_SSL=$(VERIFY_SSL) \
	   run-met-loc1
