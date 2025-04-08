"""Tests for the views."""

import re
from datetime import datetime
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


def test_create_record_via_service(app, db, location, vocabularies):
    """Test the record metadata schema."""
    from invenio_access.permissions import system_identity
    from invenio_rdm_records.proxies import current_rdm_records_service

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

    result = current_rdm_records_service.create(system_identity, raw_data)
    today = datetime.now().strftime("%Y-%m-%d")

    assert result.data["metadata"]["title"] == "Test Record"
    assert result.data["metadata"]["resource_type"]["id"] == "dataset"
    assert result.data["metadata"]["creators"][0]["person_or_org"]["name"] == "Neo"
    assert "role" not in result.data["metadata"]["creators"][0]
    assert result.data["metadata"]["publisher"] == "Imperial College London"
    assert result.data["metadata"]["publication_date"] == today
