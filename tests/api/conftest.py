"""API test fixtures."""

import pytest
from invenio_app.factory import create_api
from invenio_oauth2server.models import Token
from invenio_oauth2server.proxies import current_oauth2server


@pytest.fixture(scope="module")
def create_app():
    """Provide the Flask app object used by tests."""
    return create_api


@pytest.fixture
def api_headers(db, user_depositor):
    """Headers for API requests, including API token."""
    scopes = [s[0] for s in current_oauth2server.scope_choices()]
    token = Token.create_personal("test_token", user_depositor.id, scopes=scopes)
    db.session.commit()
    return {
        "Authorization": f"Bearer {token.access_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def api_file_upload_headers(api_headers):
    """Headers for API file upload requests, including API token."""
    return {
        **api_headers,
        "Content-Type": "application/octet-stream",
    }
