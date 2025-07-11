# Poetry Docker Plugin

<a href="https://github.com/vagmcs/poetry-docker-plugin/actions/workflows/tester.yml" target="_blank">
    <img src="https://github.com/vagmcs/poetry-docker-plugin/actions/workflows/tester.yml/badge.svg?event=push&branch=main" alt="Test">
</a>
<a href="https://results.pre-commit.ci/latest/github/vagmcs/poetry-docker-plugin/main" target="_blank">
    <img src="https://results.pre-commit.ci/badge/github/vagmcs/poetry-docker-plugin/main.svg" alt="pre-commit.ci status">
</a>
<a href="https://pypi.org/project/poetry-docker-plugin" target="_blank">
    <img src="https://img.shields.io/pypi/v/poetry-docker-plugin?color=gree&label=pypi%20package">
</a>
<a href="https://pypi.org/project/poetry-docker-plugin" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/poetry-docker-plugin?color=gree">
</a>

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

In order to install the plugin you need to have installed a poetry version `>=2.0.0` and type:

```bash
poetry self add poetry-docker-plugin
```

or add the following to your `pyproject.toml`:

```toml
[tool.poetry.requires-plugins]
poetry-docker-plugin = ">=0.x.x"
```

## License

This project is licensed under the terms of the MIT license.
