ROOT_DIR=$(shell git rev-parse --show-toplevel)
V = 0
Q = $(if $(filter 1,$V),,@)
M = $(shell printf "\033[34;1m▶\033[0m")

APP_NAME = iotics-data-{{cookiecutter.module_name}}
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
	   && docker build --build-arg VERSION=$(VERSION) -t $(APP_NAME) -f {{cookiecutter.follower_dir}}/Dockerfile .


SEED ?= "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
HOST_USER ?= "did:iotics:iotVm7Afr6bs4PdTyw6yDvT3eF9L2THTV1iM"
QAPI_URL ?= http://localhost:8081/qapi
QAPI_STOMP_URL ?= ws://localhost:8080/ws
RESOLVER_HOST ?= http://localhost:5000
VERIFY_SSL ?= False

docker-run-host: docker-build  ## Docker run of the follower against a running host (see README)
	$Q docker run --rm --network host \
		-e {{cookiecutter.conf_env_var_prefix}}QAPI_URL=$(QAPI_URL)	\
		-e {{cookiecutter.conf_env_var_prefix}}QAPI_STOMP_URL=$(QAPI_STOMP_URL)	\
		-e {{cookiecutter.conf_env_var_prefix}}AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
        -e {{cookiecutter.conf_env_var_prefix}}AUTH__SEED=$(SEED) \
        -e {{cookiecutter.conf_env_var_prefix}}AUTH__USER=$(HOST_USER) \
		-e {{cookiecutter.conf_env_var_prefix}}ROOT_LOG_LEVEL=DEBUG \
		-e {{cookiecutter.conf_env_var_prefix}}VERFIY_SSL=$(VERIFY_SSL) \
		$(APP_NAME)
run:
	$Q {{cookiecutter.conf_env_var_prefix}}ROOT_LOG_LEVEL=INFO \
	   {{cookiecutter.conf_env_var_prefix}}AUTH__RESOLVER_HOST=$(RESOLVER_HOST) \
	   {{cookiecutter.conf_env_var_prefix}}QAPI_URL=$(QAPI_URL)	\
	   {{cookiecutter.conf_env_var_prefix}}QAPI_STOMP_URL=$(QAPI_STOMP_URL)	\
	   {{cookiecutter.conf_env_var_prefix}}AUTH__SEED=$(SEED) \
	   {{cookiecutter.conf_env_var_prefix}}AUTH__USER=$(HOST_USER) \
	   {{cookiecutter.conf_env_var_prefix}}VERIFY_SSL=$(VERIFY_SSL) \
	   {{cookiecutter.command_name}}
