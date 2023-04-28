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
	@poetry run isort poetry_docker_plugin
	@poetry run black poetry_docker_plugin

### compile        : Apply code styling and perform type checks
.PHONY: compile
compile: format
	@poetry check
	@poetry run ruff poetry_docker_plugin
	@poetry run mypy poetry_docker_plugin

### build          : Compile, run tests and package
.PHONY: build
build: compile
	@poetry build

### changelog      : Create changelogs
.PHONY: changelog
	@cz changelog --file-name "docs/release_notes/${PROJECT_VERSION}.md" v${PROJECT_VERSION}
	@cat "docs/release_notes/${PROJECT_VERSION}.md" | tail -n +3 > "docs/release_notes/${PROJECT_VERSION}.md"

### publish        : Publish the package
.PHONY: publish
publish:
	@echo "Releasing version '${PROJECT_VERSION}'"
	@git tag -a v"${PROJECT_VERSION}" -m "version ${PROJECT_VERSION}"
	@git push origin v"${PROJECT_VERSION}"
	@gh release create v"${PROJECT_VERSION}" -F "docs/release_notes/${PROJECT_VERSION}.md" \
		dist/poetry_docker_plugin-${PROJECT_VERSION}.tar.gz \
		dist/poetry_docker_plugin-${PROJECT_VERSION}-py3-none-any.whl
	@poetry publish --build