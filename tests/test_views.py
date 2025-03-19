"""Tests for the views."""

import json
import os
import re
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


@pytest.fixture(scope="module")
def app_config(app_config):
    """Update invenio app_config fixture."""
    app_config["COLLECT_STORAGE"] = "flask_collect.storage.file"
    instance_path = app_config.get(
        "INSTANCE_PATH", os.environ.get("INVENIO_INSTANCE_PATH", "/tmp")
    )
    manifest_dir = os.path.join(instance_path, "static/dist")
    manifest_path = os.path.join(manifest_dir, "manifest.json")
    os.makedirs(manifest_dir, exist_ok=True)

    with open(manifest_path, "w") as f:
        json.dump(
            {
                "status": "done",
                "assets": {"theme.css": "/static/dist/theme.css"},
                "chunks": {},
                "publicPath": "/static/dist",
            },
            f,
        )

    theme_css_path = os.path.join(manifest_dir, "theme.css")
    with open(theme_css_path, "w") as f:
        f.write("/* Empty theme file */")

    app_config["WEBPACKEXT_MANIFEST_PATH"] = manifest_path
    return app_config


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
