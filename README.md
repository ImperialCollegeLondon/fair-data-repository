# Imperial Fair Data Repository

Welcome to your InvenioRDM instance.

## Getting started

As a starting point it's assumed that you have Python 3.9, [invenio-cli] and Docker
Compose installed. You should be able to run `invenio-cli check-requirements`
successfully.

### Local Installation

```console
invenio-cli install
invenio-cli services setup
invenio-cli run
```

Once the Flask server has started visit https://127.0.0.1:5000 in your browser. Once
finished, stop the running Flask server and use `invenio-cli services stop` to bring
down the running services.

Subsequently the server may be started with:

```console
invenio-cli services start
invenio-cli run
```

### Docker

Run the following commands in order to start your new InvenioRDM instance:

```console
invenio-cli containers start --lock --build --setup
```

The above command first builds the application docker image and afterwards starts the
application and related services (database, Elasticsearch, Redis and RabbitMQ). The
build and boot process will take some time to complete, especially the first time as
docker images have to be downloaded during the process.

Once running, visit https://127.0.0.1 in your browser.

**Note**: The server is using a self-signed SSL certificate, so your browser will issue
a warning that you will have to by-pass.

## Development

### QA

It is strongly recommended to use [pre-commit] to check your individual commits meet the
QA standards of the project. These are enforced via GitHub Actions and it's easiest to
make sure you're compliant as you go along. Details of the QA tools can be found in
`.pre-commit-config.yaml`.

### Continuous Integration

A simple Continuous Integration setup is provided via GitHub Actions. This checks the
target commit against the project QA tooling and for commits to the main branch builds
and pushes Docker images for the web application and frontend.

### Tests

A test suite is provided in the `tests` directory. Assuming services have already been
setup, tests can be run with:

```console
invenio services start
pipenv run pytest
```

All development work should be supported by an appropriate set of tests. Best practices
around testing are expected to evolve as the project develops.

The [pytest-invenio] plugin is provided to support test development. This extends
[pytest-flask] to provide fixtures and support for testing Invenio.

### Local Installation

The standard local installation as described in [Getting Started] is suitable for
development.

### Docker

A additional Docker Compose file is provided to give a simple development setup using
Docker. Assuming Invenio services have aleady been setup, it can be used by:

```console
invenio-cli services start
docker compose -f docker-compose.app-dev.yml up app
```

Then access https://127.0.0.1:5000 in the browser.

## Overview

Following is an overview of the generated files and folders:

| Name                      | Description                                                                  |
| ------------------------- | ---------------------------------------------------------------------------- |
| `Dockerfile`              | Dockerfile used to build your application image.                             |
| `Pipfile`                 | Python requirements installed via [pipenv](https://pipenv.pypa.io)           |
| `Pipfile.lock`            | Locked requirements (generated on first install).                            |
| `app_data`                | Application data such as vocabularies.                                       |
| `assets`                  | Web assets (CSS, JavaScript, LESS, JSX templates) used in the Webpack build. |
| `docker`                  | Example configuration for NGINX and uWSGI.                                   |
| `docker-compose.full.yml` | Example of a full infrastructure stack.                                      |
| `docker-compose.yml`      | Backend services needed for local development.                               |
| `docker-services.yml`     | Common services for the Docker Compose files.                                |
| `invenio.cfg`             | The Invenio application configuration.                                       |
| `logs`                    | Log files.                                                                   |
| `static`                  | Static files that need to be served as-is (e.g. images).                     |
| `templates`               | Folder for your Jinja templates.                                             |
| `.invenio`                | Common file used by Invenio-CLI to be version controlled.                    |
| `.invenio.private`        | Private file used by Invenio-CLI *not* to be version controlled.             |

## Documentation

To learn how to configure, customize, deploy and much more, visit the
[InvenioRDM Documentation](https://inveniordm.docs.cern.ch/).

## Configuration

This project extends the [configuration approach] used by Invenio RDM.

Inspired by Django the following changes have been made:

- Configuration is stored in the module `ic_data_repo.config`.
- The module to use as settings can be specified at runtime via the environment variable
  INVENIO_SETTINGS_MODULE. This defaults to `ic_data_repo.config`.
- The standard InvenioRDM config file (`invenio.cfg`) now contains only the necessary
  import machinery to facilitate the above.

Note that overriding settings by environment variable still works.

The default configuration is suitable for development. A production oriented settings
file is also provided in `ic_data_repo.config.production`.

## Test Data

Instructions for accessing and working with realistic test data records are provided in
the [test_data directory].

[configuration approach]: https://inveniordm.docs.cern.ch/install/configuration/
[getting started]: #getting-started
[invenio-cli]: https://github.com/inveniosoftware/invenio-cli
[pre-commit]: https://pre-commit.com/
[pytest-flask]: https://pytest-flask.readthedocs.io/en/latest/
[pytest-invenio]: https://pytest-invenio.readthedocs.io/en/latest/
[test_data directory]: ./test_data/README.md
