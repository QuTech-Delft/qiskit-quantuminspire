# Contributing

This project uses Poetry for package management and tox for managing testing/linting/documentation tools.

## Setting up a development environment

Ensure both Poetry and tox installed (using [pipx](https://github.com/pypa/pipx) is recommended):

```bash
pipx install poetry
pipx install tox
```

Install dependencies in a virtual environment (run in root of repository):

```bash
poetry install
```

## Useful tox commands

```bash
tox -e test # Run pytest
tox -e lint # Run linters
tox -e type # Run mypy
tox # Run all of above
tox -e docs # Generate documentation
```
