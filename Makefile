SHELL:=/usr/bin/env bash -euo pipefail -c
.DEFAULT_GOAL := help

CURRENT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

.PHONY: help
help:
	@echo "usage: make command"
	@echo ""
	@echo "=== [Targets] =================================================================="
	@sed -n 's/^###//p' < $(CURRENT_DIR)/Makefile | sort

### clean          : Clean build
.PHONY: clean
clean:
	@if [ -d "dist" ]; then rm -Rf $(CURRENT_DIR)/dist; fi

### format         : Format source
.PHONY: format
format:
	@poetry run isort poetry_docker_plugin
	@poetry run black poetry_docker_plugin

### compile        : Apply code styling and perform type checks
.PHONY: compile
compile: format
	@poetry check
	@poetry run flake8 --max-line-length 120 poetry_docker_plugin
	@poetry run mypy poetry_docker_plugin

### test           : Run all tests
.PHONY: test
test:
	@poetry run pytest

### build          : Compile, run tests and package
.PHONY: build
build: compile test
	@poetry build

### publish        : Publish the package
.PHONY: publish
publish:
	@poetry publish --build