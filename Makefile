SHELL:=/usr/bin/env bash -euo pipefail -c
.DEFAULT_GOAL := help

CURRENT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_VERSION:=$(shell poetry version | sed -e 's/poetry-docker-plugin[ ]//g')

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
	@poetry run isort poetry_docker_plugin tests
	@poetry run black poetry_docker_plugin tests

### compile        : Apply code styling and perform type checks
.PHONY: compile
compile: format
	@poetry check
	@poetry run ruff check --diff --no-fix poetry_docker_plugin tests
	@poetry run ruff format --check --diff poetry_docker_plugin tests
	@poetry run mypy poetry_docker_plugin tests

### test           : Run tests
.PHONY: test
test:
	@poetry run pytest

### build          : Compile, run tests and package
.PHONY: build
build: compile test
	@poetry build

_bump_version:
	@poetry version patch

### changelog      : Create changelogs
.PHONY: changelog
changelog: _bump_version
	$(eval NEXT_VERSION=$(shell poetry version | sed -e 's/poetry-docker-plugin[ ]//g'))
	@git tag -a v"${NEXT_VERSION}" -m "version ${NEXT_VERSION}"
	@cz changelog --file-name "mkdocs/docs/release_notes/${NEXT_VERSION}.md" v${NEXT_VERSION}

### publish        : Publish the package
.PHONY: publish
publish:
	$(eval NEXT_VERSION=$(shell poetry version | sed -e 's/poetry-docker-plugin[ ]//g'))
	@echo "Releasing version '${NEXT_VERSION}'"
	@poetry publish --build
	@git push origin v"${NEXT_VERSION}"
	@gh release create v"${NEXT_VERSION}" -F "mkdocs/docs/release_notes/${NEXT_VERSION}.md" \
		dist/poetry_docker_plugin-${NEXT_VERSION}.tar.gz \
		dist/poetry_docker_plugin-${NEXT_VERSION}-py3-none-any.whl
