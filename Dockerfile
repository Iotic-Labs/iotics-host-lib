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
