SHELL:=/usr/bin/env bash -euo pipefail -c
.DEFAULT_GOAL := help

CURRENT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME:=$(shell poetry version | sed -e 's/[ ].*//g' | tr '-' '_')
PROJECT_VERSION:=$(shell poetry version | sed -e 's/.*[ ]//g')
RELEASE_NOTES:=$(shell cat pyproject.toml | grep release_notes_file | sed -e 's/.*=[ ]//g')

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
	@if [ -d "docs/site" ]; then rm -Rf $(CURRENT_DIR)/docs/site; fi

### format         : Format source
.PHONY: format
format:
	@poetry run pyupgrade --py39-plus **/*.py || true
	@poetry run isort $(PROJECT_NAME) tests
	@poetry run ruff format $(PROJECT_NAME) tests
	@poetry run docformatter $(PROJECT_NAME) tests || true

### compile        : Apply code styling and perform type checks
.PHONY: lint
lint:
	@poetry check
	@poetry run ruff check --fix $(PROJECT_NAME) tests
	@poetry run mypy $(PROJECT_NAME) tests

### test           : Run tests
.PHONY: test
test:
	@poetry run pytest

### build          : Run tests, build docs and package
.PHONY: build
build: test
	@poetry build
	@poetry run mkdocs build -f docs/mkdocs.yml

### local-docs     : Run local documentation server
.PHONY: local-docs
local-docs: build
	@mkdocs serve -f docs/mkdocs.yml

### docker         : Build docker image
.PHONY: docker
docker:
	@poetry docker

### bump           : Bump version and generate changelog (INCREMENT can be PATCH, MINOR or MAJOR)
.PHONY: bump
bump:
	@cz changelog --template docs/templates/release_notes.j2 --file-name $(RELEASE_NOTES)
	@cz bump --yes --increment $(INCREMENT)

### release        : Release the package and documentation
.PHONY: release
release: build
	@echo "Releasing version '$(PROJECT_VERSION)'"
	@poetry publish
	@poetry run mkdocs gh-deploy
	@gh release create \
		--verify-tag $(PROJECT_VERSION) \
		--notes-file $(RELEASE_NOTES) \
		dist/$(PROJECT_NAME)-$(PROJECT_VERSION).tar.gz \
		dist/$(PROJECT_NAME)-$(PROJECT_VERSION)-py3-none-any.whl
