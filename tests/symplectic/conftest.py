"""Symplectic test fixtures."""

import pytest
from invenio_app.factory import create_api


@pytest.fixture(scope="module")
def create_app():
    """Provide the Flask app object used by tests."""
    return create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    """Provide a valid API endpoint and a distinct retry limit."""
    app_config["SYMPLECTIC_API_URL"] = "https://api.symplectic.example.com"
    app_config["SYMPLECTIC_API_SUBSCRIPTION_KEY"] = "test-key"
    app_config["SYMPLECTIC_API_AUTH_HEADER"] = "Subscription-Key"
    app_config["SYMPLECTIC_MAX_RATE_LIMIT_RETRIES"] = 0
    return app_config
