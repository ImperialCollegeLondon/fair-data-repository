# Getting Started

Testing and development so far has only been done on native Linux. MacOS is supported by
InvenioRDM but has not been tested with this project. Development in WSL may be possible
but working natively in Windows is not supported.

## Requirements

The requirements for working with InvenioRDM are laid out in detail in the
[InvenioRDM System Requirements Docs]. You're ready to go once you have cloned the code
repository and can run `invenio-cli check-requirements --development` in the project
directory and all requirements are met. Below are some tips and specifics for this
project:

- Start by installing `invenio-cli` and run the requirements check above to see what's
    missing.
- Both `pipenv` and `invenio-cli` are best installed with [pipx]. These need to be
    discoverable on your path.
- We are currently pinning to Python 3.9 for compatibility to the deployment base image
    so you'll need this available. `invenio-cli` will be satisfied with anything 3.9 or
    newer but you need 3.9.
- Cairo and DejaVu are listed in the InvenioRDM Docs but are not checked for by
    `invenio-cli`. The direct impacts of not having these is unclear but you'd probably
    get by.
- ImageMagik is checked for by `invenio-cli` but similarly you'd probably get by without
    it.

## Tooling Overview

A combination of tools are used to manage the project. Their different roles are
summarised below but most operations use `invenio-cli` which wraps the other tools as
required and is covered in more detail below.

- `pipenv` is used to manage Python dependencies and the virtual environment used for
    development.
- `node` and `npm` are used to manage JavaScript dependencies and the build process for
    the frontend.
- Docker and Docker Compose are used to manage the services required to run the
    application, namely the database, OpenSearch, Redis and RabbitMQ.
- `invenio` - is the core application of InvenioRDM. Whilst a few operations require
    invoking it directly it mostly called indirectly via `invenio-cli`. It is installed
    within the virtual environment managed by `pipenv` so must be invoked via
    `pipenv run invenio`.

### `invenio-cli`

As mentioned above `invenio-cli` is the primary tool for managing the project in
development and most operations are performed by invoking it. It's main subcommands are
sumarised below:

- `invenio-cli install` - Installs the project and its dependencies. Creates the virtual
    environment if necessary, syncs the dependencies with Pipfile.lock, builds the
    frontend and copies/symlinks the assets to the correct location in the virtual
    environment.
- `invenio-cli services` - Manages the Docker services required to run the application.
    Can be used to setup, start, stop and teardown the services.
- `invenio-cli run` - Starts the Flask development server and a set of Celery workers.
    Note that in development this should always be used rather than `invenio run` as
    this passes appropriate configuration.
- `invenio-cli packages` - Wraps `pipenv` to manage Python dependencies. Can be used to
    install, uninstall and update packages.
- `invenio-cli pyshell` - Starts a shell in the virtual environment with an initialised
    Flask app.
- `invenio-cli assets` - Manages static files and frontend assets. Can be used to build
    the frontend, watch for changes and clean up.

## Local Installation

Initial setup of the project can be done with the following commands:

```console
invenio-cli install
invenio-cli services setup --no-demo-data
```

This will:

- Create a virtual environment and install the Python dependencies. `site/ic_data_repo`
    is installed in editable mode so changes to the source code are immediately
    available.
- Install the JavaScript dependencies and build the frontend assets.
- Copy/symlink the staticfiles and Javascript assets to the correct location in the
    virtual environment.
- Start the Docker services required to run the application and ensure they are healthy.
    This includes the database, OpenSearch, Redis and RabbitMQ.
- Create the database schema, initialise the Opensearch indices and various other
    one-off setup tasks.
- Populate the database with some default data e.g. default user roles and permissions.
    The `--no-demo-data` flag is used to prevent the creation of demo data records.
    Remove it if you want the instance to be populated with example deposit data.
- Creates a number of Celery tasks to populate the database with controlled vocabulary
    data. Note that there are no Celery workers running yet to process these tasks so
    they are just waiting in a queue.

Note that the above leaves the services running. You can stop them with
`invenio-cli services stop`. Either way you can then start the Flask server with:

```console
invenio-cli run
```

This runs the Flask development server and creates a number of Celery workers in the
background. If the services are not already running then they will be started. The first
time this is run after setup there will be a backlog of Celery tasks that starts
executing. This can be a bit resource intensive and make things a bit sluggish.

Once the Flask server has started visit <https://127.0.0.1:5000> in your browser. The
development setup uses a self-signed TLS certificate so may need to bypass a security
warning. Once finished, stop the running Flask server and use
`invenio-cli services stop` to bring down the running services.

If you want to restart the setup process from scratch you can use
`invenio-cli services destroy` remove all the services and data.

### Logging In

In order to log in to the application you will need to create a user account:

```console
invenio users create DUMMY_EMAIL --password DUMMY_PASSWORD --active
```

You can also optionally make this user an admin with:

```console
invenio access allow administration-access user DUMMY_EMAIL
```

### Imperial Single Sign-On and Microsoft Graph API Access

To be able to log in using Imperial SSO use functionality relating to the Microsoft
graph API the following environment variables must be set: `ICL_OAUTH_CLIENT_ID` and
`ICL_OAUTH_CLIENT_SECRET`. Appropriate values for use in development are available from
the Imperial password safe. Ask Chris C-A for access.

Direct links:

- [ICL_OAUTH_CLIENT_ID]
- [ICL_OAUTH_CLIENT_SECRET]

### Creating deposits

You will not be able to create a new upload (or access the deposit page via the UI
links) until you have created a community to contain the records. This community must
have the id "icl" but its other properties are unimportant. The easiest way to create a
community is via the UI at <https://127.0.0.1:5000/communities/new>.

## Development

### QA

[pre-commit] is a tool for running automated checks whenever you make a new commit. If
you don't already have it installed pre-commit is included along with the development
dependencies of the project. If you have a separate installation of pre-commit you can
set it up to check your individual commits with `pre-commit install`. If you're using
pre-commit from the development dependencies then you can set it up
`pipenv run pre-commit install`. Note that in this later case you may need to run this
command again if the pipenv managed virtual environment changes.

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
invenio-cli services start
pipenv run pytest
```

### End-to-end UI tests

- Start services and server:
    - `invenio-cli services start`
    - `invenio-cli run`
- Run Selenium e2e:
    - `pipenv run pytest tests/e2e`

All development work should be supported by an appropriate set of tests. Best practices
around testing are expected to evolve as the project develops.

The [pytest-invenio] plugin is provided to support test development. This extends
[pytest-flask] to provide fixtures and support for testing Invenio.

### Backend Development

Using `invenio-cli run` will start the Flask development server and a set of Celery
workers. Debugging is enabled and it the server will automatically reload when changes
are made to the source.

### Frontend Development

The frontend is built with Webpack and the assets are managed by `invenio-cli`. Any
changes made to the css or javascript assets will require a rebuild of the assets. As a
one-off operation this can be done with `invenio-cli assets build`. To watch for changes
and rebuild automatically use `invenio-cli assets watch`.

Note that the above is not required for any changes to the html templates which are
processed by the backend.

### Troubleshooting

InvenioRDM is a sophisticated application with many moving parts. If you encounter
issues the below information may help with troubleshooting:

- `invenio-cli` stores some state about the project (e.g. whether setup has been
    performed for the services) in the file `.invenio.private`. The file is gitignored
    but avoid deleting it. If you're worried it has gotten out of sync then run
    `invenio-cli destroy` to completely remove all services, data and resources.
- If you encounter errors about missing indexes (for Opensearch) or database tables (for
    postgres) then setup may not have completed successfully. You can try
    `invenio-cli services destroy` to do a complete teardown then setup the services
    again.
- You can check the status of the services with `invenio-cli services status`. This will
    show which services are running and whether they are healthy. If a service is having
    issues you can use Docker Compose to check the logs e.g.
    `docker compose logs opensearch`.
- The celery workers started by `invenio-cli run` can be a bit verbose and polute the
    logs in the console. You can redirect the celery logs to a file with
    `invenio-cli run --celery-log-file /path/to/logfile`.
- `invenio-cli pyshell` can be used to start a shell in the virtual environment with an
    initialised Flask app. This can be useful for debugging issues with the application
    code or inspecting config.

### Symplectic Integration

Symplectic Elements is a research management system that constructs a graph connecting
researchers, awards and research outputs (publications, including datasets). While it
can import metadata from various sources, it lacks native support for InvenioRDM
repositories.

The system uses relationships to associate publications with researchers and their roles
(author, contributor, etc.). These relationships are required for publications to appear
in a researcher's Symplectic UI and can be declined if incorrect.

Our integration consists of two main components:

1. **API Client Interface** (`SymplecticClient`) - Converts InvenioRDM record metadata
    into Symplectic's required XML format and handles API communication via PUT
    requests.

1. **Service Component Hook** - Automatically triggers the `export_record_to_symplectic`
    task when records are published or updated, seamlessly integrating Symplectic
    export into the publication workflow.

## Configuration

This project extends the [configuration approach] used by Invenio RDM.

Inspired by Django the following changes have been made:

- Configuration is stored in the module `ic_data_repo.config`.
- The module to use as settings can be specified at runtime via the environment variable
    `INVENIO_SETTINGS_MODULE`. This defaults to `ic_data_repo.config`.
- The standard InvenioRDM config file (`invenio.cfg`) now contains only the necessary
    import machinery to facilitate the above.

Note that overriding settings by environment variable still works.

The default configuration is suitable for development. A production oriented settings
file is also provided in `ic_data_repo.config.production`.

## Test Data

!!! note
    This functionality is not currently working.

Instructions for accessing and working with realistic test data records are provided in
the [test_data directory].

[configuration approach]: https://inveniordm.docs.cern.ch/install/configuration/
[icl_oauth_client_id]: https://icsecpws.cc.ic.ac.uk:443/GetPassCard.cc?ACCOUNTID=456013&ORGN_NAME=MSP
[icl_oauth_client_secret]: https://icsecpws.cc.ic.ac.uk:443/GetPassCard.cc?ACCOUNTID=456012&ORGN_NAME=MSP
[inveniordm system requirements docs]: https://inveniordm.docs.cern.ch/install/requirements/
[pipx]: https://pipx.pypa.io/stable/
[pre-commit]: https://pre-commit.com/
[pytest-flask]: https://pytest-flask.readthedocs.io/en/latest/
[pytest-invenio]: https://pytest-invenio.readthedocs.io/en/latest/
[test_data directory]: https://github.com/ImperialCollegeLondon/fair-data-repository/blob/develop/test_data/README.md
