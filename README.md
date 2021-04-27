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

Install Cookiecutter, see [__Installation__](https://cookiecutter.readthedocs.io/en/latest/installation.html)


### Create a template of a connector

From `iotics-host-lib` root folder run the following command if you want to create a __Publisher__ template:

```shell
cookiecutter builder/iotics/publisher_template/
```

or run the following command if you want to create a __Follower__ template:

```shell
cookiecutter builder/iotics/follower_template/
```

then follow instructions on terminal.

### Example of usage

```bash
$ cookiecutter builder/iotics/publisher_template/

project_name [A project name used in the doc (ex: Random Temperature Generator)]: Random Temperature Generator
publisher_dir [publisher_directory_name (ex: random-temp-pub)]: random-temp-pub
module_name [python module name (ex: randpub)]: randpub
command_name [command line name (ex: run-randpub)]: run-randpub
conf_env_var_prefix [conf environment variable prefix (ex: RANDPUB_)]: RANDPUB_
publisher_class_name [publisher class name (ex: RandomTempPublisher)]: RandomTempPublisher
Select add_example_code:
1 - YES
2 - NO
Choose from 1, 2 [1]: 1
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

Once you have created a Connector with the Cookiecutter the README.md in that connector's folder will guide you on building and running it.


#### Iotics host common library
Version compatibility with Iotics host:

| iotics-host-lib | iotics-host |
| ---: | --- |
| `>=2.0.11` | `~=1.1` |
| `>=3.0` | `>=2.0.350` |


## Iotics Internal Links

[Build Status](https://build.cor.corp.iotic/go/pipeline/activity/iotics-host-lib)

[![Built with Mage](https://magefile.org/badge.svg)](https://magefile.org)
