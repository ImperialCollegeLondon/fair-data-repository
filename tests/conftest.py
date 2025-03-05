"""Global test fixtures."""

import pytest
from invenio_app.factory import create_app


@pytest.fixture(scope="module")
def app(db_uri):
    """Provide the Flask app object used by tests."""
    app = create_app()

    # blank out sqlalchemy options as the defaults (inherited from
    # invenio_app_rdm.config) contain "pool_timeout" which is not valid for use with
    # the test sqlite database
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    # Use a temporary database for testing.
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

    with app.app_context():
        yield app
