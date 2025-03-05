"""Global test fixtures."""

import pytest
from invenio_app.factory import create_app


@pytest.fixture(scope="module")
def app():
    """Provide the Flask app object used by tests."""
    app = create_app()
    with app.app_context():
        yield app
