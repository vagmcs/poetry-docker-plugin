# Poetry Docker Plugin

[![License: LGPL v3](https://img.shields.io/badge/License-MIT-blue.svg)](https://mit-license.org)
![PyPI](https://img.shields.io/pypi/v/poetry-docker-plugin?color=gree&label=pypi%20package)
![PyPI](https://img.shields.io/pypi/pyversions/poetry-docker-plugin?color=gree)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

[Poetry](https://python-poetry.org) docker plugin is an extension for configuring and building docker images directly from the comfort of your `pyproject.toml` configuration.

The key features are:

* Easy and similar to Dockerfile syntax support.
* Easily generate dockerfiles, build them and push them to any registry.
* Multiple docker image support. You can declare and build multiple images from a single project.
* Supports configuration variables on image declaration that can be set at runtime.
* Multi-platform build support.

---

**Documentation**: <a href="https://vagmcs.github.io/poetry-docker-plugin" target="_blank">https://vagmcs.github.io/poetry-docker-plugin </a>

---

## Installation

In order to install the plugin you need to have installed a poetry version `>=1.8.0` and type:

```bash
poetry self add poetry-docker-plugin
```

## License

This project is licensed under the terms of the MIT license.