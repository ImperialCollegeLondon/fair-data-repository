"""Tests for the views."""

import re
from datetime import date
from unittest.mock import patch

import pytest
from ic_data_repo.permissions import deposit_action
from invenio_access.permissions import ActionUsers
from invenio_oauth2server.models import Token
from invenio_oauth2server.proxies import current_oauth2server


@pytest.fixture
def user(UserFixture, app, db):
    """An initialised user."""
    u = UserFixture(
        email="foo@bar.com",
        password="password",
    )
    u.create(app, db)
    return u


@pytest.fixture
def user_client(user, client):
    """A client logged in as the user fixture."""
    return user.login(client)


@pytest.fixture
def user_depositor(user, db):
    """Give the user fixture permission to create deposits."""
    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))
    return user


@pytest.fixture(autouse=True)
def mock_manifest():
    """Mock manifest to always return a value for theme.css."""
    with patch("flask_webpackext.manifest.JinjaManifest.__getitem__") as mock:
        mock.return_value = '<link rel="stylesheet" href="/static/dist/theme.css">'
        yield mock


def test_index_view(client):
    """Simple check that index view does not give an error when rendered."""
    res = client.get("/")
    assert res.status_code == 200
    assert b"Imperial College London" in res.data


def test_index_auth(user_client, app):
    """Check the index view with a logged in user."""
    res = user_client.get("/")

    assert res.status_code == 200

    # find any instances of the new upload url that don't include the community
    # parameter, regex negative lookahead magic
    assert not re.search(r"/uploads/new(?!\?community=icl)", res.data.decode("utf-8"))


@pytest.fixture
def browser_headers(user_client):
    """Headers for web browser requests, including CSRF token."""
    csrf_token = user_client.get_cookie("csrftoken").value
    if not csrf_token:
        raise ValueError("CSRF token not found in cookies")
    return {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token,
    }


@pytest.fixture
def api_headers(db, user_client, user_depositor):
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


@pytest.fixture
def access():
    """Simple access schema."""
    return {
        "record": "public",
        "files": "public",
    }


def test_metadata_schema(
    client, location, vocabularies, user_depositor, api_headers, metadata, access
):
    """Test that the metadata schema is enforced."""
    metadata["resource_type"] = "fake_resource_type"
    metadata["publisher"] = "Fake Publisher"
    metadata["publication_date"] = "1970-01-01"
    access["record"] = "restricted"
    access["files"] = "restricted"
    result = client.post(
        "/api/records",
        json={"metadata": metadata, "access": access},
        headers=api_headers,
    )
    assert result.status_code == 201

    # Test metadata policies are enforced.
    assert result.json["metadata"]["title"] == "Test Record"
    assert result.json["metadata"]["resource_type"]["id"] == "dataset"
    assert (
        result.json["metadata"]["creators"][0]["person_or_org"]["given_name"] == "Neo"
    )
    assert "role" not in result.json["metadata"]["creators"][0]
    assert result.json["metadata"]["publisher"] == "Imperial College London"
    assert result.json["metadata"]["publication_date"] == date.today().isoformat()

    # Test access policies are enforced.
    # 'record' should be reset to public, but 'files' should remain restricted.
    assert result.json["access"]["record"] == "public"
    assert result.json["access"]["files"] == "restricted"


def test_metadata_schema_rights(
    client, location, vocabularies, user_depositor, api_headers, metadata
):
    """Test that the rights schema is enforced."""
    # Test that no license is accepted.
    metadata["rights"] = []
    result = client.post(
        "/api/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert "rights" not in result.json["metadata"]

    # Test that a single license is accepted.
    metadata["rights"] = [{"id": "cc0-1.0"}]
    result = client.post(
        "/api/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert result.json["metadata"]["rights"][0]["id"] == "cc0-1.0"

    # Test that multiple rights entries are not accepted.
    metadata["rights"] = [{"id": "cc0-1.0"}, {"id": "cc-by-4.0"}]
    result = client.post(
        "/api/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert result.json["errors"][0]["messages"][0].startswith("No more than")


def test_deposit_view_permissions(user, user_client, db, vocabularies, app):
    """Check that only users with deposit permissions can access the deposit page."""
    # permission denied initially
    response = user_client.get("/uploads/new")
    assert response.status_code == 403

    # grant access to the user
    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))

    # page now accessible
    response = user_client.get("/uploads/new")
    assert response.status_code == 200


def test_ui_changes_for_depositors(user, user_client, db):
    """Check that the UI changes for users with deposit permissions."""
    # As seen by non-depositors.
    res = user_client.get("/")
    assert res.status_code == 200

    # Check that non-depositor information is shown.
    assert re.search(r"You have read-only access.", res.data.decode("utf-8"))

    # Check that the deposit button is not visible.
    assert not re.search(r"quick-create-dropdown", res.data.decode("utf-8"))

    # As seen by depositors.
    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))
    res = user_client.get("/")
    assert res.status_code == 200

    # Check that non-depositor information is not shown.
    assert not re.search(r"You have read-only access.", res.data.decode("utf-8"))

    # Check that the deposit button is visible.
    assert re.search(r"quick-create-dropdown", res.data.decode("utf-8"))
