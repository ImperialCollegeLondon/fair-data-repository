"""API test fixtures."""

import pytest
from invenio_access.permissions import system_identity
from invenio_app.factory import create_api
from invenio_communities.proxies import current_communities


@pytest.fixture(scope="module")
def create_app():
    """Provide the Flask app object used by tests."""
    return create_api


@pytest.fixture(autouse=True)
def icl_community(db, location):
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
    community = current_communities.service.create(system_identity, data)
    db.session.commit()
    return community


@pytest.fixture
def metadata():
    """Simple record metadata."""
    return {
        "title": "Test Record",
        "description": "This is a test record.",
        "resource_type": {"id": "dataset"},
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
        "rights": [{"id": "cc-by-4.0"}],
    }
