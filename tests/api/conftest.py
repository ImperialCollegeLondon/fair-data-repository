"""API test fixttures."""

import pytest
from invenio_app.factory import create_api


@pytest.fixture(scope="module")
def create_app():
    """Provide the Flask app object used by tests."""
    return create_api
