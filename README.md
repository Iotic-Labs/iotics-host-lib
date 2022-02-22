# iotics-host-lib

Iotics host library - a library to aid integration with Iotics

This library is a Python wrapper which abstracts calls to our Python `iotic.web.rest.client`, `iotic.web.stomp` and
`iotic.lib.identity` client libraries. Note: the REST and STOMP interfaces can instead be used directly to integrate
with Iotics if preferred, e.g. if using another language other than Python.

In addition, this library also provides a way for developers to generate boilerplate code for what Iotics calls
__Connectors__, by using [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/README.html).
Connectors are what we call the __Publishers__ that push/publish data into Iotics, and the __Followers__ that
receive/follow data out of Iotics. Once you have followed the steps in this README to add example code, and then
followed the steps in the READMEs of the generated Connectors, you will have created and run a fully functioning
example.

## Iotics Basics

All data that is published into Iotics is done so in association with a particular _Digital Twin_, a virtual
representation of something in the real world. Anything that exists -- a person, device, data source, whatever -- can
have an Iotic Twin made, giving it an [identity](https://www.w3.org/TR/did-core/) which is then semantically described
with metadata properties.  In this example, we create Iotic Twins for a thermometer (the publisher) and someone
interested in its readings (the follower).

Each Digital Twin may expose one or more _Feeds_, where it publishes its real-time streaming data. Having successfully
searched for and found a publisher twin of interest, a follower twin may subscribe to a feed and receive updates as they
are published. By adding _Values_ to these Feeds you may make clear what sort of data is present in each update.

The example publisher Connector creates a twin and shares random temperatures, the example follower Connector creates
its own twin then finds and follows the publisher twin's feed logging the temperatures as they are shared by the
publisher. Once you generate these Connectors following the steps below, you'll find a README in each Connector's
folder. This README will point out the important parts of the Connector's code and guide you through building and
running its program.

Having created a working example using the cookiecutter, you could now obviously alter the generated code to integrate
with your own data sources.

## Create a new Iotics Connector with Cookiecutter

### Requirements

- Install Python, see  [__Installation__](https://www.python.org/downloads/)
- Install Cookiecutter, see [__Installation__](https://cookiecutter.readthedocs.io/en/latest/installation.html)

### Create a template of a connector

>Note: For Windows users in order for cookiecutter to complete the template creation, before running the command remove the `post_gen_project.py` from both follower_template and publisher_template in the `iotics-host-lib/builder/iotics/` directory.

From `iotics-host-lib` root folder run the following command if you want to create a __Publisher__ template:

```shell
cookiecutter builder/iotics/publisher_template/
```

or run the following command if you want to create a __Follower__ template:

```shell
cookiecutter builder/iotics/follower_template/
```

then follow instructions on terminal.

>Note: To generate the default example with sample code, press the `Enter` key for all options without providing any input.

### Example of usage

```bash
$ cookiecutter builder/iotics/publisher_template/

project_name [A project name used in the doc (ex: Random Temperature Generator)]: 
publisher_dir [publisher directory name (ex: random-temp-pub)]: 
module_name [python module name (ex: randpub)]: 
command_name [command line name (ex: run-rand-pub)]: 
conf_env_var_prefix [conf environment variable prefix (ex: RANDPUB_)]: 
publisher_class_name [publisher class name (ex: RandomTempPublisher)]: 
Select add_example_code:
1 - YES
2 - NO
Choose from 1, 2 [1]: 
```

The following structure is created:

```bash
├── random-temp-pub
│   ├── Dockerfile
│   ├── Makefile
│   ├── randpub
│   │   ├── conf.py
│   │   ├── exceptions.py
│   │   ├── __init__.py
│   │   └── publisher.py
│   ├── README.md
│   ├── setup.cfg
│   ├── setup.py
│   ├── tests
│   │   └── unit
│   │       └── randpub
│   │           ├── conftest.py
│   │           ├── __init__.py
│   │           ├── test_conf.py
│   │           └── test_publisher.py
│   ├── tox.ini
│   └── VERSION

4 directories, 15 files
```

### Building and running

Once you have created a Connector with the Cookiecutter the README.md in that connector's folder will guide you on
building and running it.

### Monitoring and alerting

For metrics, the library is using [Prometheus'](https://prometheus.io/docs/introduction/overview/) official
[Python client](https://github.com/prometheus/client_python). The following describes an example of how to monitor your
component locally. After your components are set up to expose endpoints to scrape (see READMEs of the generated
Connectors for more details), create `prometheus.yml` config file:

```yaml
# https://prometheus.io/docs/prometheus/latest/configuration/configuration/#configuration-file
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  # - "rules.yml"

scrape_configs:
  # Here it's Prometheus itself.
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'
    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.
    static_configs:
    - targets: ['localhost:9101']

  - job_name: 'random-temp-pub'
    static_configs:
    - targets: ['localhost:8001']

  - job_name: 'random-temp-fol'
    static_configs:
    - targets: ['localhost:8002']
```

Next you can start Prometheus server locally with e.g.:

```bash
docker run --rm --name prometheus --network host -v"$(realpath ./prometheus.yml)":/prometheus/prometheus.yml prom/prometheus --web.listen-address=:9101
```

Note that:

- if you remove `--rm` flag you can persist the data after stopping the container and restart it with:

  ```bash
  docker start -a prometheus
  ```

- `--network host` usage is not recommended on a production environment
  ([additional info](https://docs.docker.com/network/host/));
- if the default Prometheus port (`9090`) is already being used, you can change it with the argument from the end:  
  `--web.listen-address=:9101` but that will change the config file it uses
  from `/etc/prometheus/prometheus.yml` to `/prometheus/prometheus.yml`.

#### Data visualisation

For data visualisation and export we recommend trying out Grafana's 
[Docker](https://grafana.com/grafana/download?pg=get&platform=docker&plcmt=selfmanaged-box1-cta1) image:

```bash
docker run --rm --name grafana --network host grafana/grafana
```

Note that `--network host` should not be used on a production environment.

Visit http://localhost:3000/ and use `admin` as login and password, next navigate to: "Configuration" ->
"Add data source" and "Select" the Prometheus (or click [here](http://localhost:3000/datasources/new)).
In the "URL" field paste `http://localhost:9101` and press "Save & Test", you should see: `Data source is working`
if everything is set up correctly.

In the "Explore" view you can use for example the following queries to see Random Temperature Connectors:

- general metrics of Random Temperature Publisher and Follower (per-second rate):  
  `rate(api_call_count{job=~"random-temp-.*"}[1m])`
  ([link](http://localhost:3000/explore?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Prometheus%22,%7B%22exemplar%22:true,%22expr%22:%22rate(api_call_count%7Bjob%3D~%5C%22random-temp-.*%5C%22%7D%5B1m%5D)%22,%22requestId%22:%22Q-1a2a6156-415b-42fa-98b1-6fd3c18be6ee-0A%22%7D%5D));
- Random Temperature Publisher number of feed publishes that failed as measured over the last minute:  
  `increase(api_call_count{job="random-temp-pub", function="share_feed_data", failed="True"}[1m])`
  ([link](http://localhost:3000/explore?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Prometheus%22,%7B%22exemplar%22:true,%22expr%22:%22increase(api_call_count%7Bjob%3D%5C%22random-temp-pub%5C%22,%20function%3D%5C%22share_feed_data%5C%22,%20failed%3D%5C%22True%5C%22%7D%5B1m%5D)%22,%22requestId%22:%22Q-7830e1fd-158f-4b22-8f89-707bb8b83547-0A%22%7D%5D)).

#### OSX notes

The `--network host` flag is not supported on Docker Desktop for Mac.

Instead you can : -

- Run prometheus: - `docker run -p 9101:9090 --rm --name prometheus -v"$(realpath ./prometheus.yml)":/prometheus/prometheus.yml prom/prometheus:latest --config.file=/prometheus/prometheus.yml`
- Run grafana: - `docker run --rm --name grafana -p 3000:3000 grafana/grafana`
- When configuring the prometheus datasource in grafana set the URL to `http://docker.for.mac.host.internal:9101`
- Make the prometheus configuration file point to host using `docker.for.mac.host.internal`

```yaml
...
scrape_configs:
  # Here it's Prometheus itself.
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'
    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.
    static_configs:
    - targets: ['localhost:9090']

  - job_name: 'random-temp-pub'
    static_configs:
    - targets: ['docker.for.mac.host.internal:8001']

  - job_name: 'random-temp-fol'
    static_configs:
    - targets: ['docker.for.mac.host.internal:8002']
```

## Testing FAQ

- When running `make unit-tests` in the top level of this repo you can get the error `AssertionError: assert 'Max retries exceeded with' in ''` if you are running the iotics host locally. The solution is to run `make docker-clean-test` on the local host and the tests should all pass.

## Iotics host common library

Version compatibility with Iotics host:

| iotics-host-lib | iotics-host |
|----------------:| --- |
|      `>=2.0.11` | `~=1.1` |
|         `>=3.0` | `>=2.0.350` |
|         `>=7.0` | `>=3.0.692` |
|         `>=8.0` | `>=3.0.725` |

## Iotics Internal Links

[Build Status](https://build.cor.corp.iotic/go/pipeline/activity/iotics-host-lib)  
[![Built with Mage](https://magefile.org/badge.svg)](https://magefile.org)

## Release Process

- Before merging the new change to master, set the new version major or minor numbers in 2 places [here](https://github.com/Iotic-Labs/dev-gocd-pipelines/blob/aeb1d3c3ac2b308697247bbe5d53b63264dfa271/iotics-host-lib.gocd.yaml#L5) and [here](https://github.com/Iotic-Labs/dev-gocd-pipelines/blob/aeb1d3c3ac2b308697247bbe5d53b63264dfa271/iotics-host-lib.gocd.yaml#L106) in the pipeline file, and merge the changed pipeline file to main.
    - Use [semantic versioning](https://semver.org/); when there is a breaking change increase the first (major) number. When there are compatible non breaking changes increase the second (minor) number. For backwards compatible bug fixes the third (patch) number will be increased automatically by the {count} in the pipeline file.
- When you merge the host-lib change into master then the pipeline will create a new version on nexus [here](https://nexus.cor.corp.iotic/#browse/browse:py-internal:iotics-host-lib-sources). Download this new version and add it and any other iotics dependency changes (e.g. iotic.web.rest.client - also download from nexus) to the [deps folder](https://github.com/Iotic-Labs/iotics-host-lib/tree/master/deps) and remove any older versions and dependencies.
- The pipeline automatically tags the master branch with the version number after it has run. However you need to manually update the version number in the VERSION file to match this tag to be the same as the version of the host lib you have put in the deps folder.
- Create a release note blog post by pressing on the + sign next to Blogs on the lhs [here](https://ioticlabs.atlassian.net/wiki/spaces/RN/overview), making sure to add the `iotic-host-lib` label, adding this label will then also create an entry [here](https://ioticlabs.atlassian.net/wiki/spaces/RN/pages/439025665/iotics-host-lib+Release+Notes), as well as the blog post.

