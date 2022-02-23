# Copyright 2022 Iotic Labs Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Iotic-Labs/iotics-host-lib/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
FROM quay.io/iotic_labs/iotics-python-base-38 as builder
ARG PIP_INDEX_URL
RUN test -n "$PIP_INDEX_URL" || (echo "--build-arg PIP_INDEX_URL not set" && false)

# install build dependencies
RUN apt-get update && apt-get install -y curl
# add sources

COPY ./dist /dist

# get certificate
RUN curl -k -s -o /corp.iotic.ca.pem https://ca.cor.corp.iotic/ca.pem
RUN pip config set global.trusted-host nexus.cor.corp.iotic

# install the solution
RUN pip3 install  -i $PIP_INDEX_URL --cert /corp.iotic.ca.pem -f /dist \
    --no-cache-dir --prefix /install /dist/iotics.host.lib-*.whl

# cleanup
RUN find /install -name '*.c' -delete
RUN find /install -name '*.pxd' -delete
RUN find /install -name '*.pyd' -delete
RUN find /install -name '__pycache__' | xargs rm -r
