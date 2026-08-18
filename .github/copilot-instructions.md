# Copilot Instructions

## Project Overview

**Helix** is an [InvenioRDM](https://inveniordm.docs.cern.ch/) instance customised for Imperial College London, deployed as a research data repository (FAIR data). It supports dataset-only deposits with a centralised review/approval workflow and Imperial SSO login.

## Tech Stack

- **Python 3.12** with Pipenv for dependency management
- **InvenioRDM ~13.0** (Flask-based, with Celery, PostgreSQL, Redis, RabbitMQ, OpenSearch)
- **Docker / Docker Compose** for local services
- **Helm** for Kubernetes (AKS) deployment
- **MkDocs + Material** for documentation (in `docs/`)

## Project Structure

```
/                        # Root: Pipfile, invenio.cfg, docker-compose files
  site/
    ic_data_repo/        # Main Python package (InvenioRDM extension)
      config/            # Environment-specific config modules
      auth/              # Imperial SSO OAuth integration
      symplectic/        # Symplectic Elements integration
      permissions.py     # Custom access/deposit permissions
      views.py           # Blueprint views
      tasks.py           # Celery tasks
      imperial_schema.py # Custom metadata schema (datasets only)
  tests/                 # Pytest tests (unit + integration, no e2e by default)
  app_data/              # Controlled vocabularies and application data
  test_data/             # Scripts to seed realistic test data
  templates/             # Jinja2 template overrides
  assets/                # Frontend asset overrides
  docs/                  # MkDocs documentation source
```

## Build & Run Commands

```bash
# Create Python virtual environment, symlink static content and build frontend assets
invenio-cli install

# Start backend services (PostgreSQL, Redis, RabbitMQ, OpenSearch)
invenio-cli services start

# Run tests (excludes e2e)
pipenv run pytest -p no:warnings -m "not e2e"

# Run e2e tests only
pipenv run pytest -m e2e

# Build documentation
pipenv run mkdocs build

# Run Python commands with an intialised flask app
pipenv run invenio shell -c "print(app.config)"
```

## Configuration

`invenio.cfg` loads settings from the module specified by `INVENIO_SETTINGS_MODULE` (default: `ic_data_repo.config`). Override per environment by pointing to a different module in `site/ic_data_repo/config/`.

## Code Conventions

- **Formatter**: `black` (line length 88), **import sorter**: `isort`
- **Linter**: `flake8` with `flake8-docstrings` (Google docstring convention)
- **Type checking**: `mypy` (strict generics; run via pytest-mypy)
- **Python style**: `pyupgrade --py312-plus`
- Pre-commit hooks enforce all of the above; run `pre-commit install` after checkout
- Tests live in `tests/`; use `testcontainers` for integration tests requiring services

## Key Entry Points

- `site/setup.cfg` — package entry points (blueprints, Celery tasks, Webpack, extensions)
- `ic_data_repo/ext.py` — `ImperialExtension` and `SymplecticExt` Flask extensions
- `ic_data_repo/permissions.py` — `deposit_action` and custom permission policies

## Knowledge Base

Furter detailed documentation to support AI agents is provided in the
`docs/knowledge_base` directory. Read this before starting any development task. Start
with `index.md`, and selectively pull in further information as required based on user
requests.
