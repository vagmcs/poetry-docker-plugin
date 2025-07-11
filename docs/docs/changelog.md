## 0.5.4

### Build

- 🔧Adds support for poetry 2.
- 🔧Bumps minimum python version to 3.9.
- 🔧Updates dependencies.

## 0.5.3

### Fixes

- 🐛Proper support for [`package_mode`](https://python-poetry.org/docs/pyproject#package-mode).

## 0.5.2

### Fixes

- 🐛Fixes multi-platform push command.

### Documentation

- 📜Adds links to release notes.

### Build

- 🔧Adds tests.


## 0.5.1

### Documentation

- 📜Renames `image_tags` to `tags`.

### Fixes

- 🐛Properly support python version ranges.
- 🐛Raises error for undefined user variables.

### Build

- 🔧Adds Makefile commands for generating changelog and publishing the project.

## 0.5.0

### Features

- ✨Adds proper multi-platform support.
- ✨Adds `dockerfile-only` command line option for generating the Dockerfiles without building the images.
- ✨Adds `arg` CLI option for defining build arguments.
- ✨Adds `build-only` argument for building a subset of images (when multiple images are configured).
- ✨Adds support for multiple tags.
- ✨Adds support for build-in variables:
  - Project name `@(name)` and version `@(version)`.
  - Python version `@(py_version)`.
  - Commit SHA `@(sha)`.
- ✨Adds `var` CLI option for user-defined variables
- ✨Adds `push` CLI option for pushing images

### Fixes

- 🐛Corrects python version parsing.

### Build

- 🔧Moves commitizen configuration inside `pyproject.toml`.
- 🔧Updates dependency versions.
- 🔧Adds a git push tag command to Makefile.


## 0.4.0

### Features

- ✨Adds support for multi-image builds.
- ✨Adds custom dockerfile name support.
- ✨Adds support for platforms.
- ✨Automatically decide python base package.

### Documentation

- 📜Includes a simple example in README.md.
- 📜Adds docstrings for instructions.

### Fixes

- 🐛Fixes support for author multiple names
- 🐛Fixes author name parsing regex
- 🐛Uses double quotes on CMD and ENTRYPOINT commands
