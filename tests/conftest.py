"""Global test fixtures."""

import pytest
from invenio_app.factory import create_app as app_factory


@pytest.fixture(scope="module")
def app_config(app_config):
    """Update invenio app_config fixture."""
    # blank out sqlalchemy options as the defaults (inherited from
    # invenio_app_rdm.config) contain "pool_timeout" which is not valid for use with
    # the test sqlite database
    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = ""
    return app_config


@pytest.fixture(scope="module")
def create_app():
    """Provide the Flask app object used by tests."""
    return app_factory
