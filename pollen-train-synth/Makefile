ROOT_DIR=$(shell git rev-parse --show-toplevel)
V = 0
Q = $(if $(filter 1,$V),,@)
M = $(shell printf "\033[34;1m▶\033[0m")

APP_NAME = iotics-data-pollentrainsynth
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
	   && docker build --build-arg VERSION=$(VERSION) -t $(APP_NAME) -f pollen-train-synth/Dockerfile .


# SEED ?= "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
# HOST_USER ?= "did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM"
# QAPI_URL ?= http://localhost:8081/qapi
# QAPI_STOMP_URL ?= ws://localhost:8080/ws
# RESOLVER_HOST ?= http://localhost:5000
# VERIFY_SSL ?= False

SEED ?= "3ac858269b62e7d21fb38cc29636f2e9b6114283cc2c99fd3dbe7dad511bfca0"
HOST_USER ?= "did:iotics:iotEZK1EpLXozpNmMmiT5VyCjc4peexQSpdt"
QAPI_URL_F ?= https://dte-rrps.iotics.space/qapi
QAPI_STOMP_URL_F ?= wss://dte-rrps.iotics.space/ws
RESOLVER_HOST ?= https://did.prd.iotics.com
VERIFY_SSL ?= False


QAPI_URL_P ?= https://enterprise-dev.iotics.space/qapi
QAPI_STOMP_URL_P ?= wss://enterprise-dev.iotics.space/ws

docker-run: docker-build  ## Docker run of the follower against a running host (see README)
	$Q docker run --rm --network host \
		-e POLLENTRAINSYNTH_QAPI_URL=$(QAPI_URL)	\
		-e POLLENTRAINSYNTH_QAPI_STOMP_URL=$(QAPI_STOMP_URL)	\
		-e POLLENTRAINSYNTH_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
        -e POLLENTRAINSYNTH_AUTH__SEED=$(SEED) \
        -e POLLENTRAINSYNTH_AUTH__USER=$(HOST_USER) \
		-e POLLENTRAINSYNTH_ROOT_LOG_LEVEL=DEBUG \
		-e POLLENTRAINSYNTH_VERFIY_SSL=$(VERIFY_SSL) \
		$(APP_NAME)
run:
	$Q POLLENTRAINSYNTHF_ROOT_LOG_LEVEL=INFO \
	   POLLENTRAINSYNTHF_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
	   POLLENTRAINSYNTHF_QAPI_URL=$(QAPI_URL_F)	\
	   POLLENTRAINSYNTHF_QAPI_STOMP_URL=$(QAPI_STOMP_URL_F)	\
	   POLLENTRAINSYNTHF_AUTH__SEED=$(SEED) \
	   POLLENTRAINSYNTHF_AUTH__USER=$(HOST_USER) \
	   POLLENTRAINSYNTHF_VERIFY_SSL=$(VERIFY_SSL) \
	   POLLENTRAINSYNTHP_ROOT_LOG_LEVEL=INFO \
	   POLLENTRAINSYNTHP_AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
	   POLLENTRAINSYNTHP_AUTH__SEED=$(SEED) \
	   POLLENTRAINSYNTHP_AUTH__USER=$(HOST_USER) \
	   POLLENTRAINSYNTHP_VERIFY_SSL=$(VERIFY_SSL) \
	   POLLENTRAINSYNTHP_QAPI_URL=$(QAPI_URL_P)	\
	   POLLENTRAINSYNTHP_QAPI_STOMP_URL=$(QAPI_STOMP_URL_P)	\
	   run-pollentrain-synth
