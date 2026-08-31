"""API test fixttures."""

import pytest
from ic_data_repo.permissions import deposit_action
from invenio_access.permissions import ActionUsers, system_identity
from invenio_app.factory import create_api
from invenio_communities.proxies import current_communities
from invenio_oauth2server.models import Token
from invenio_oauth2server.proxies import current_oauth2server
from invenio_requests.proxies import current_requests_service


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
def icl_community(db):
    """Create the Imperial College London community."""
    data = {
        "slug": "icl",
        "metadata": {
            "title": "Imperial College London",
            "description": "The Imperial College London community.",
        },
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
            "review_policy": "members",
        },
    }
    community = current_communities.service.create(identity=system_identity, data=data)
    db.session.commit()
    return community


@pytest.fixture
def accept_request(db):
    """Provides a function for accepting requests."""

    def _accept(request_id):
        current_requests_service.execute_action(
            system_identity,
            request_id,
            "accept",
            data={},
        )
        db.session.commit()

    return _accept
