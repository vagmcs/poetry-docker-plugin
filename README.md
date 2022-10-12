# Poetry Docker Plugin

[![License: LGPL v3](https://img.shields.io/badge/License-MIT-blue.svg)](https://mit-license.org)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

A [Poetry](https://python-poetry.org) plugin for configuring and building docker images directly from python projects.

## Installation

In order to install the plugin you need to have installed a poetry version `>1.0` and type:

```bash
poetry self add poetry-docker-plugin
```

## Usage

Add the following section to your pyproject.toml:

```toml
[tool.docker]
image_name = "org/custom_image:latest" # docker image name
args = { arg1 = "", version = "1.2.0" } # default values for args
from = "python:3.9"
labels = { "com.github.vagmcs"="Awesome", "description"="This is a test image", "version"="0.1.0" }
copy = [
    { source = "./poetry-docker-plugin-0.1.0.tar.gz", target = "/opt/pdp.tar.gz" },
#    { source = "../pyproject.toml", target = "/tmp/pp.toml" }
]
env.SERVICE_OPTS = "-Xms1g -Xmx2g -XX:+DoEscapeAnalysis -XX:+OptimizeStringConcat -XX:+DisableAttachMechanism"
env.SERVICE_CONFIGURATION = "/opt/service.conf"
volume = ["/data"]
flow = [
    { work_dir = "/opt" },
    { run = "ls" },
    { work_dir = "/tmp" },
    { run = "ls /opt" },
]
expose = [8888, 9999]
cmd = ["run_service", "--verbose"]
entrypoint = ""
```

then, as soon as you are done configuring, type:

```bash
poetry docker
```

## License

This project is licensed under the terms of the MIT license.