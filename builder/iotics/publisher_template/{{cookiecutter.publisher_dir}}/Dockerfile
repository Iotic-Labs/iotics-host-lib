FROM alpine:3.12 as builder
ARG REST_PYTHON_VERSION="3.8"
ARG VERSION
ENV VERSION=$VERSION

# install build dependencies
RUN apk add --update --no-cache python3-dev~=$REST_PYTHON_VERSION \
    linux-headers \
    g++ \
    py-pip \
    curl \
    libressl-dev \
    musl-dev \
    libffi-dev \
    cargo

# add sources
COPY {{cookiecutter.publisher_dir}}/{{cookiecutter.module_name}} /sources/{{cookiecutter.module_name}}
RUN mkdir /deps
COPY deps/ /deps/
COPY {{cookiecutter.publisher_dir}}/setup.* /sources/

# install the solution
ENV PYTHONPATH=$PYTHONPATH:/install/lib/python3.8/site-packages/
RUN pip3 install -U pip setuptools
RUN pip3 install -f /deps --no-cache-dir --ignore-installed --prefix /install /sources

# cleanup
RUN find /install -name '*.pyc' -delete
RUN find /install -name '__pycache__' -delete

FROM alpine:3.12
ARG REST_PYTHON_VERSION="3.8"
# run package dependencies
RUN apk add --no-cache python3~=$REST_PYTHON_VERSION libressl libffi

# get prebuilt sources and libraries
COPY --from=builder /sources /sources
COPY --from=builder /install/lib /usr/local/lib
COPY --from=builder /install/bin/{{cookiecutter.command_name}} /usr/local/bin/

# run setup
WORKDIR /sources
ENV PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.8/site-packages/
CMD {{cookiecutter.command_name}}
