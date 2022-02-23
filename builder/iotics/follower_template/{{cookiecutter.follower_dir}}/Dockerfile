# Copyright © 2021 to 2022 IOTIC LABS LTD. info@iotics.com
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
FROM python:3.8.8-slim-buster as builder
ARG VERSION
ENV VERSION=$VERSION

# add sources
COPY {{cookiecutter.follower_dir}}/{{cookiecutter.module_name}} /sources/{{cookiecutter.module_name}}
RUN mkdir /deps
COPY deps/ /deps/
COPY {{cookiecutter.follower_dir}}/setup.* /sources/

# install the solution
RUN pip3 install -U pip setuptools
RUN pip3 install -f /deps --no-cache-dir --ignore-installed --prefix /install /sources

# cleanup
RUN find /install -name '*.pyc' -delete
RUN find /install -name '__pycache__' -delete


FROM python:3.8.8-slim-buster
# get prebuilt sources and libraries
COPY --from=builder /sources /sources
COPY --from=builder /install/lib /usr/local/lib
COPY --from=builder /install/bin/{{cookiecutter.command_name}} /usr/local/bin/

# run setup
WORKDIR /sources
ENTRYPOINT ["{{cookiecutter.command_name}}"]
