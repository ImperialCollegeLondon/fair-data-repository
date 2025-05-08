"""Tests for the views."""

import re
from datetime import date
from unittest.mock import patch

import pytest


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


def test_metadata_schema(user_client, location, vocabularies):
    """Test the record metadata schema."""
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": get_csrf_token(user_client),
    }

    raw_data = {
        "metadata": {
            "title": "Test Record",
            "resource_type": "fake_resource_type",
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "name": "Neo",
                    },
                    "role": "the one",
                },
            ],
            "publisher": "Fake Publisher",
            "publication_date": "1970-01-01",
        },
    }

    result = user_client.post(
        "/api/records",
        json=raw_data,
        headers=headers,
    )

    assert result.status_code == 201
    assert result.json["metadata"]["title"] == "Test Record"
    assert result.json["metadata"]["resource_type"]["id"] == "dataset"
    assert result.json["metadata"]["creators"][0]["person_or_org"]["name"] == "Neo"
    assert "role" not in result.json["metadata"]["creators"][0]
    assert result.json["metadata"]["publisher"] == "Imperial College London"
    assert result.json["metadata"]["publication_date"] == date.today().isoformat()


def test_new_record_version(user_client, location, vocabularies):
    """Test creating a new version of a record."""
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": get_csrf_token(user_client),
    }

    record_metadata = {
        "files": {"enabled": False},
        "access": {"record": "public", "files": "public"},
        "metadata": {
            "title": "Test Record",
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
            "publisher": "Fake Publisher",
            "publication_date": "1970-01-01",
        },
        "custom_fields": {
            "imperial:dart_id": "123456789",
        },
    }

    create_draft_request = user_client.post(
        "/api/records",
        json=record_metadata,
        headers=headers,
    )

    assert create_draft_request.status_code == 201

    draft_id = create_draft_request.json["id"]

    community_metadata = {
        "slug": "icl",
        "metadata": {
            "title": "Physics Research Group",
        },
        "access": {
            "visibility": "public",
        },
    }

    create_community_response = user_client.post(
        "/api/communities",
        json=community_metadata,
        headers=headers,
    )

    community_uuid = create_community_response.json["id"]
    assert create_community_response.status_code == 201

    community_submission_request_metadata = {
        "receiver": {"community": community_uuid},
        "type": "community-submission",
    }

    create_request_response = user_client.put(
        f"/api/records/{draft_id}/draft/review",
        json=community_submission_request_metadata,
        headers=headers,
    )

    assert create_request_response.status_code == 200
    assert create_request_response.json["id"] is not None
    assert "submit" in create_request_response.json["links"]["actions"]

    request_id = create_request_response.json["id"]

    submit_review_request = user_client.post(
        f"/api/records/{draft_id}/draft/actions/submit-review",
        headers=headers,
    )

    assert submit_review_request.status_code == 202
    assert "accept" in submit_review_request.json["links"]["actions"]

    accept_submission_request = user_client.post(
        f"/api/requests/{request_id}/actions/accept", headers=headers
    )

    assert accept_submission_request.status_code == 200
    assert accept_submission_request.json["status"] == "accepted"
