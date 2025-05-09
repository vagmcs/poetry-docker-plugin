# Poetry Docker Plugin

![PyPI](https://img.shields.io/pypi/v/poetry-docker-plugin?color=gree&label=pypi%20package)
![PyPI](https://img.shields.io/pypi/pyversions/poetry-docker-plugin?color=gree)

[Poetry](https://python-poetry.org) docker plugin is an extension for configuring and building docker images directly from the comfort of your `pyproject.toml` configuration.

The key features are:

* Easy and similar to Dockerfile syntax support.
* Easily generate dockerfiles, build them and push them to any registry.
* Multiple docker image support. You can declare and build multiple images from a single project.
* Supports configuration variables on image declaration that can be set at runtime.
* Multi-platform build support.

## Installation

In order to install the plugin you need to have installed a poetry version `>=1.2.0` and type:

```bash
poetry self add poetry-docker-plugin
```

That it, you are ready to go!

## Quickstart

Let's assume that you have created a Poetry project, running a simple service. The service is implemented inside the `app` package in the `__main__.py` source file. Then, your poetry `pyproject.toml` configuration may look as follows:

```toml
[tool.poetry]
name = "simple_service"
version = "1.0.0"
description = "A simple service."
authors = ["Evangelos"]

[tool.poetry.dependencies]
python = "3.11"

[tool.poetry.scripts]
service = "app.__main__:start"
```

Since the script `service` is declared in the `[tool.poetry.scripts]` section, the service can be run by typing the following command:

```bash
poetry run service
```

Then, simply by adding the following 3 lines in the `pyproject.toml` configuration you can build a docker image that runs the service in port 8000.

```toml
[tool.docker]
expose = [8000]
cmd = ["service"]
```

To build the image, just type:

```bash
poetry docker
```

Phew, that was easy!

There are a couple of things to note here:

1. Since no tag is provided for the image, the plugin automatically derives one from the declared authors and project name. In our case the default tag should be `evangelos/simple_service:latest`.

2. Since no base image is provided, the plugin automatically infers and uses the python version declared inside `pyproject.toml`, in our case `python:3.11`.

3. The plugin automatically packages the project, copies the distribution into the docker container and installs all dependencies. Therefore, all entrypoints declared in `pyproject.toml`, such as `service` are accessible inside the docker image!

Of course, you can customize all that, as we shall see shortly.

Finally, if you are curious to inspect the underlying Dockerfile before building it, just type:

```bash
poetry docker --dockerfile-only
```

## Configuration Overview

Poetry docker plugin supports most of the commands you can use in a [Dockerfile](https://docs.docker.com/engine/reference/builder). Here is a full configuration the demonstrates all available commands:

```toml
[tool.docker]
tags = [
    "evangelos/simple_service:1.0.0",
    "evangelos/simple_service:latest",
]
args = { python_version = "3.11" }
from = "python:${python_version}"
labels = { "description" = "A simple service." }
copy = [
    # a sequence of COPY commands
    { source = "application.conf", target = "/package/application.conf" },
]
env.LOG_LEVEL = "DEBUG"
env.ENABLE_METRICS = "true"
volume = ["/data"]
flow = [
    # a sequence of WORKDIR and RUN commands
    { work_dir = "/package" },
    { run = "python -m spacy download en_core_web_sm" },
]
expose = [8888, 9999]
cmd = ["service", "--verbose"] # you may also use entrypoint = []
```

* `tags` declare a list of tags for the resulting image.
* `args` declare Dockerfile [arguments](https://docs.docker.com/engine/reference/builder/#arg) and their default values. Default values are mandatory.
* `from` declares the base image. If [from](https://docs.docker.com/engine/reference/builder/#from) command is omitted, the plugin automatically figures out the python version of the project and use it as the base image.
* `labels` declare a dictionary of metadata for the image.
* `copy` declares a list of dictionaries, each one having only a `source` and a `target` key-value pair that performs a [copy](https://docs.docker.com/engine/reference/builder/#copy) command inside the docker container.
* `env` declares environment variables inside the docker image.
* `volume` declares a list of mount points to be used for holding externally mounted volumes.
* `flow` declares a list of `workdir`, `user` and `run` docker commands.
* `expose` exposes a list of ports.
* `cmd` and/or `entrypoint` declare a list holding the executable of the image and its arguments.


as soon as you are done configuring, type:

```bash
poetry docker
```

when the build is finished, validate that the image tags are available by typing:

```bash
docker images
```

## Multiple docker images

In a number of projects, there are multiple modules, and thus, it is necessary to build more than one docker images from the project sources. For instance, machine learning engineers often need to build one image for training a model, and one for the service deployed in production after the training has been completed. To that end, `poetry-docker-plugin` supports multi-docker image configurations.

Consider the following simple example of a machine learning project configuration:

```toml
[tool.poetry]
name = "example_ml_project"
version = "1.0.0"
description = "An example ML project."
authors = ["Evangelos"]

[tool.poetry.dependencies]
python = "3.11"

[tool.poetry.scripts]
service = "app.__main__:start"
trainer = "trainer.__main__:start"
```

Note that the project declares one poetry script that starts a service, and another one that runs the training job. The plugin allows us to easily declare one docker configuration for each script, as follows:

```toml
[tool.docker.service]
expose = [8000]
cmd = ["service"]

[tool.docker.trainer]
cmd = ["trainer"]
```

To build both images type:

```bash
poetry docker
```

The plugin should detect both configurations and build separate images for the service and the trainer. Each of these configurations has its own Dockerfile and thus can be fully configured using the commands described in the [Configuration Overview](#configuration-overview).

> You may build only one of the declared images by providing the `--build-only` option in the `poetry docker` command (see [Command line options](#command-line-options) for more details).

## Build-in and user-defined variables

Poetry docker plugin provides a few build-in variables that can be used in the `pyproject.toml` configuration to facilitate the maintainability of the declared images. Currently, there are four build-in variables:

* **@(name)**: the name of the project.
* **@(version)**: the version of the project.
* **@(py_version)**: the python version.
* **@(sha)**: the commit 7-byte SHA-256, in case the project is a git repository.

These variables may be used anywhere in the `[tool.docker]` section of `pyproject.toml` and they should be replaced by their actual value during the build process. For instance,

```toml
[tool.docker]
tags = [
    "org/@(name):latest",
    "org/@(name):@(version)",
    "org/@(name):@(sha)"
]
from = "python:@(py_version)"
expose = [8888]
cmd = ["service"]
```

this configuration should build an image using as base image the python version declared in the `pyproject.toml`, which is identical to the default case, that is, when `from` command is not provided. The build should create three tags,

1. `org/example_ml_project:latest`
2. `org/example_ml_project:1.0.0`
3. `org/example_ml_project:7515162`

The plugin also allows user-defined variables through the command line options. For example, lets assume that you would like to build separate images for development and production environments and you use to declare that in the image tag. Then, your `image_tag` section may looks as follows:

```toml
[tool.docker]
tags = [
    "org/@(context)/@(name):latest",
    "org/@(context)/@(name):@(version)",
    "org/@(context)/@(name):@(sha)"
]
expose = [8888]
cmd = ["service"]
```

By default, the plugin does not know the value for the variable **@(context)**. However, you can provide the value using the command line option `--var`. For instance, in order to tag the image for the development context you may type:

```bash
poetry docker --var=context:dev
```

then, the plugin should produce the following three tags:

1. `docker.io/dev/example_ml_project:latest`
2. `docker.io/dev/example_ml_project:1.0.0`
3. `docker.io/dev/example_ml_project:7515162`

## Build arguments

The plugin supports docker build arguments using the `args` command. These arguments can be used in the docker image configuration using the standard bash variable syntax `${VAR}`. For example consider an image that we would like to build for different python versions.

```toml
[tool.docker]
args = { python_version = "@(py_version)" }
tags = [
    "org/@(context)/@(name):latest",
    "org/@(context)/@(name):@(version)",
    "org/@(context)/@(name):@(sha)"
]
from = "python:${python_version}"
expose = [8888]
cmd = ["service"]
```

Note that by default the value of the argument `python_version` is the value of the build-in variable **@(py_version)**, which equals to the project version. However, the `python_version` argument value can changed using the command line option `--arg`, which is similar to the option `--var`.

> Docker build arguments and user-defined variables may seem very similar and you may argue that variables are not useful. In practice, variables provide a way to access important values declared in the `pyproject.toml` from inside the Dockerfile. Moreover, they provide a way to dynamically declare docker tags which are not declared inside the Dockerfile.

## Multi-platform builds

Often, there is a need to build images for a different target platform than the one building the image or even cross-build images for multiple platforms. The most common use case I think is both for `linux/amd64` and `linux/arm64`. The plugin provides a simple command line option:

```bash
poetry docker --platform linux/amd64 --platform linux/arm64
```

## Command-Line options

All command line options provided by the `poetry-docker-plugin` may be accessed by typing:

```bash
poetry docker --help
```
    --dockerfile-only          Creates Dockerfile, but does not build the image.
    --build-only[=BUILD-ONLY]  Builds only selected images. (multiple values allowed)
    -p, --platform[=PLATFORM]  Sets a target platform. (multiple values allowed)
    --exclude-package          Does not install project package inside docker container.
    --push                     Pushes the image to the registry.
    -r, --var[=VAR]            Declares a custom variable using the syntax 'name:value'. Then, the variable can be used in the docker configuration using: @(name). (multiple values allowed)
    -a, --arg[=ARG]            Declares a build argument using the syntax 'name:value' (multiple values allowed)

## License

This project is licensed under the terms of the MIT license.
