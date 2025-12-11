"""API test fixttures."""

import pytest
from ic_data_repo.permissions import deposit_action
from invenio_access.permissions import ActionUsers
from invenio_app.factory import create_api
from invenio_oauth2server.models import Token
from invenio_oauth2server.proxies import current_oauth2server


@pytest.fixture(scope="module")
def create_app():
    """Provide the Flask app object used by tests."""
    return create_api


@pytest.fixture
def user_depositor(user, db):
    """Give the user fixture permission to create deposits."""
    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))
    return user


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
def metadata():
    """Simple record metadata."""
    return {
        "title": "Test Record",
        "description": "This is a test record.",
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "given_name": "Neo",
                    "family_name": "Anderson",
                },
                "role": "the one",
            },
        ],
    }
