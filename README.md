# Poetry Docker Plugin

[![License: LGPL v3](https://img.shields.io/badge/License-MIT-blue.svg)](https://mit-license.org)
![PyPI](https://img.shields.io/pypi/pyversions/poetry-docker-plugin)
![PyPI](https://img.shields.io/pypi/v/poetry-docker-plugin?color=gree&label=pypi%20package)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

A [Poetry](https://python-poetry.org) plugin for configuring and building docker images directly from python projects.

## Installation

In order to install the plugin you need to have installed a poetry version `>=1.3.0` and type:

```bash
poetry self add poetry-docker-plugin
```

## Simple Example

Let's assume that you have created a Poetry project having the following `pyproject.toml` configuration:

```toml
[tool.poetry]
name = "example_project"
version = "1.0.0"
description = "An example poetry project."
authors = ["Evangelos"]

[tool.poetry.dependencies]
python = "3.11"

[tool.poetry.scripts]
run_service = "app.service:start"
```

your project also declares a poetry script that starts a service. Then, by adding the following minimal docker configuration in your `pyproject.toml` you can build your docker image:

```toml
[tool.docker]
expose = [8000]
cmd = ["run_service"]
```

Note that there is no docker [FROM](https://docs.docker.com/engine/reference/builder/#from)  command, and thus `poetry-docker-plugin` automatically figures out the python version and use `python:3.11` as the base image. Moreover, since we have not defined a name for the image, it derives one, using the first author name and the project name. Thus, by running the command `poetry docker`, poetry builds a docker image ready to run your service in port `8000`. Under the hood, `poetry-docker-plugin` automatically packages the project, copy the distribution into the docker container and installs all dependencies.
 
## Docker Configuration Skeleton

The configuration below outlines all supported commands:

```toml
[tool.docker]
image_name = "org/image_name:version"
args = { version = "1.2.0" } # default values for args
from = "python:3.11"
labels = { "description" = "Poetry docker plugin is awesome." }
copy = [
    { source = "./poetry-docker-plugin-0.1.0.tar.gz", target = "/opt/pdp.tar.gz" },
]
env.SERVICE_CONFIGURATION = "/opt/service.conf"
volume = ["/data"]
flow = [
    # a sequence of WORKDIR and RUN commands
    { work_dir = "/opt" },
    { run = "ls" },
    { work_dir = "/tmp" },
    { run = "ls /opt" },
]
expose = [8888, 9999]
# alternatively you may use entrypoint = []
cmd = ["run_service", "--verbose"]
```

then, as soon as you are done configuring, type:

```bash
poetry docker
```

## Multiple Docker Images

In many projects, we would like to build more than one docker images from our project. For instance, Machine Learning engineers often need to build one image for the training procedure and one for service deployed in production after the training has been completed. To that end, `poetry-docker-plugin` supports multi-docker image configurations. 

Consider again the following simple example:

```toml
[tool.poetry]
name = "example_project"
version = "1.0.0"
description = "An example poetry project."
authors = ["Evangelos"]

[tool.poetry.dependencies]
python = "3.11"

[tool.poetry.scripts]
run_service = "app.service:start"
run_trainer = "trainer:start"
```

Note that the project now declares two poetry scripts, one that starts a service, and another one that runs some kind of training job. Then, we can define two docker configurations, one for each script, as follows:

```toml
[tool.docker.service]
expose = [8000]
cmd = ["run_service"]

[tool.docker.trainer]
cmd = ["run_trainer"]
```

By running `poetry docker`, the `poetry-docker-plugin` will detect both configurations and build two separate images, one for the service and one for the trainer.

## Command-Line Options:

The `docker` command provided by the `poetry-docker-plugin` has a couple of useful options. You can read about them by typing:

```bash
poetry docker --help
```

## License

This project is licensed under the terms of the MIT license.