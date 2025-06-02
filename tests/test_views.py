"""Tests for the views."""

import re
from datetime import date
from unittest.mock import patch

import pytest
from ic_data_repo.permissions import deposit_action
from invenio_access.permissions import ActionUsers


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


def get_csrf_token(client):
    """Get the CSRF token from the client cookie jar."""
    for cookie in client.cookie_jar:
        if cookie.name == "csrftoken":
            return cookie.value
    raise ValueError("CSRF token not found in cookies")


@pytest.fixture
def record_json():
    """JSON data for creating records via the API."""
    return {
        "metadata": {
            "title": "Test Record",
            "description": "record description",
            "resource_type": "fake_resource_type",
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "Neo",
                    },
                    "role": "the one",
                },
            ],
            "publisher": "Fake Publisher",
            "publication_date": "1970-01-01",
        },
        "access": {
            "record": "restricted",
            "files": "restricted",
        },
        "files": {"enabled": False},
    }


@pytest.fixture
def request_headers(user_client):
    """Request headers required for post/putting with user client."""
    return {
        "Content-Type": "application/json",
        "X-CSRFToken": get_csrf_token(user_client),
    }


def test_imperial_schema(
    user_client, request_headers, location, vocabularies, user_depositor, record_json
):
    """Test the custom schemas."""
    result = user_client.post(
        "/api/records",
        json=record_json,
        headers=request_headers,
    )

    assert result.status_code == 201

    # Test metadata policies are enforced.
    assert result.json["metadata"]["title"] == "Test Record"
    assert result.json["metadata"]["resource_type"]["id"] == "dataset"
    assert result.json["metadata"]["creators"][0]["person_or_org"]["name"] == "Neo"
    assert "role" not in result.json["metadata"]["creators"][0]
    assert result.json["metadata"]["publisher"] == "Imperial College London"
    assert result.json["metadata"]["publication_date"] == date.today().isoformat()

    # Test access policies are enforced.
    # 'record' should be reset to public, but 'files' should remain restricted.
    assert result.json["access"]["record"] == "public"
    assert result.json["access"]["files"] == "restricted"


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


@pytest.mark.parametrize(
    "dart_value,error",
    (
        ("", True),
        ("etet", True),
        ("123 - some text", True),
        ("123 ", False),
        ("123", False),
    ),
)
def test_dart_id_validation(
    dart_value,
    error,
    user_client,
    request_headers,
    location,
    vocabularies,
    user_depositor,
    record_json,
):
    """Check that invalid dart id values are caught by record validation.

    Although different validators are failing for different dart_value's the app always
    reports the same error message. Expected messages are displayed in the UI.
    """
    record_json["custom_fields"] = {"imperial:dart_id": dart_value}
    response = user_client.post(
        "/api/records",
        json=record_json,
        headers=request_headers,
    )
    draft_id = response.json["id"]
    publish_response = user_client.post(
        f"/api/records/{draft_id}/draft/actions/publish", headers=request_headers
    )
    if error:
        assert (
            dict(
                field="custom_fields.imperial:dart_id",
                messages=["DART ID is required."],
            )
            in publish_response.json["errors"]
        )
    else:
        assert (
            publish_response.json["custom_fields"]["imperial:dart_id"]
            == dart_value.strip()
        )
