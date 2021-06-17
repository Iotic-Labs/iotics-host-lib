FROM python:3.8.8-slim-buster as builder
ARG VERSION
ENV VERSION=$VERSION

# add sources
COPY pollen-train-synth/pollentrainsynth /sources/pollentrainsynth
RUN mkdir /deps
COPY deps/ /deps/
COPY pollen-train-synth/setup.* /sources/

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
COPY --from=builder /install/bin/run-pollentrain-synth /usr/local/bin/

# run setup
WORKDIR /sources
ENTRYPOINT ["run-pollentrain-synth"]
