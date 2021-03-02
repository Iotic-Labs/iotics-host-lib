# iotics-host-lib

Iotics host library - a library to aid integration with Iotics

This library is a Python wrapper which abstracts calls to our Python `iotic.web.rest.client`, `iotic.web.stomp` and `iotic.lib.identity` client libraries. Note: the REST and STOMP interfaces can instead be used directly to integrate with Iotics if preferred, e.g. if using another language other than Python.


In addition this library also provides a way for developers to generate boilerplate code for what Iotics call Connectors, by using [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/README.html). Connectors are what we call components that push/publish data into Iotics (a type of Connector called a __Publisher__) or receive/follow data out of Iotics (a type of Connector called a __Follower__).

By the end of following the steps in this README and selecting to add example code, then next following the steps in the READMEs of the generated Connectors, you will have created and run a fully functioning example. This example demonstrates the basics of publishing data into Iotics and receiving data out of Iotics.

The example publisher Connector creates a twin and shares random letters, the example follower Connector creates its own twin then finds and follows the publisher twin's feed logging the letters as they are shared by the publisher. The READMEs in the folders of the two Connectors that you create point out the important parts of the Connector's code and guide you through building and running the Connectors.

The symmetry of the publisher and the follower having their own twins allows their interaction to be brokered and so provides an extra level of security - for more details please refer to the Iotics [Key Concepts](https://docs.iotics.com/docs/key-concepts#brokered-interactions) documentation.

Having created a working example using the cookiecutter, you could now obviously alter the generated code to integrate with your own data sources.


## Create a new Iotics Connector with Cookiecutter

### Requirements

Install Cookiecutter, see [__Installation__](https://cookiecutter.readthedocs.io/en/latest/installation.html)
Docker to run ioticsctl utility to create keys, see [__Installation__](https://docs.docker.com/get-docker/)


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

project_name [A project name used in the doc (ex: Random Letter Generator)]: Random Letter Generator
publisher_dir [publisher_directory_name (ex: random-let-pub)]: random-let-pub
module_name [python module name (ex: randpub)]: randpub
command_name [command line name (ex: run-randpub)]: run-randpub
conf_env_var_prefix [conf environment variable prefix (ex: RANDPUB_)]: RANDPUB_
publisher_class_name [publisher class name (ex: RandomLetPublisher)]: RandomLetPublisher
Select add_example_code:
1 - YES
2 - NO
Choose from 1, 2 [1]: 1
```
The following structure is created:

```bash
├── random-let-pub
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
