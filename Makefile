~/.$(USER).env:
	@echo "Loading user env vars"
-include ~/.$(USER).env

.PHONY: Makefile
Makefile:
	@echo "Updating makefile"

# Copyright (c) 2020 Iotic Labs Ltd. All rights reserved.
export GONOSUMDB=github.com/Iotic-Labs
export GOPRIVATE=github.com/!iotic-!labs/*
export DOCKER_RUN_USER = $(shell id -u):$(shell id -g)
export PIP_INDEX_URL=https://${NEXUS_USERNAME}:${NEXUS_PASSWORD}@nexus.cor.corp.iotic/repository/py-group/simple
export DOCKER_TAG_NAME=iotic-host-base
export VERSION=${GO_PIPELINE_LABEL:-dev}

MAGE = go run magebuild/mage.go -d magebuild

mage:
	@$(MAGE) $(args)

.DEFAULT:
	@$(MAGE) -v $@

help:
	@$(MAGE)

DOCKER_NAME=
.PHONY: setup-dev

setup-dev: ## Setup the dev environment
	@ echo dev > ./src/VERSION
	@ echo dev > ./testing/VERSION
	@ echo dev > ./builder/VERSION
	@ pip install -i $(PIP_INDEX_URL) \
					--cert ${SSL_CERT_FILE} \
					-e testing/.[lint] \
					-e builder/. \
					-e src/.[dev,lint,test]

unit-static-tests: setup-dev ## Run unit and static tests locally
	@ VERSION=dev CURL_CA_BUNDLE=${SSL_CERT_FILE} \
	PIP_INDEX_URL=$(PIP_INDEX_URL) tox -vv

unit-tests: setup-dev ## Run only unit tests locally
	@ VERSION=dev CURL_CA_BUNDLE=${SSL_CERT_FILE} \
	PIP_INDEX_URL=$(PIP_INDEX_URL) tox -vv -e py3 -- $(TEST_ARGS)

static-checks: setup-dev ## Run only static tests locally
	@ VERSION=dev CURL_CA_BUNDLE=${SSL_CERT_FILE} \
	PIP_INDEX_URL=$(PIP_INDEX_URL) tox -vv -e flake8,pylint

docker-login:
	@ $(MAGE) this:login



try-pkg:
	@ rm -rf ./dist
	@ VERSION=1.2.3 ./build_all.sh
	@ docker run -v $(CURDIR):/in \
	-e PIP_INDEX_URL=$(PIP_INDEX_URL) \
	-it python:3.8 bash -c 'curl -k -s -o /corp.iotic.ca.pem https://ca.cor.corp.iotic/ca.pem &&\
	cd /in/dist && \
	rm -rf *.tar.gz && \
	pip3 install  -i $$PIP_INDEX_URL --cert /corp.iotic.ca.pem -f . ./iotics.host.lib-1.2.3-py3-none-any.whl[testing,builder] &&\
	 bash'


try-dev: ## Setup the dev environment
	@ pip install -i $(PIP_INDEX_URL) \
					--cert ${SSL_CERT_FILE} \
					-f ./dist ./dist/iotics.host.lib-dev-py3-none-any.whl[testing,builder]

