"""Placeholder module for tests of view functions."""

import os
import re

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


@pytest.fixture(scope="module")
def app_config(app_config):
    """Update invenio app_config fixture."""
    app_config["COLLECT_STORAGE"] = "flask_collect.storage.file"
    return app_config


@pytest.fixture(autouse=True)
def mock_webpack(monkeypatch):
    """Completely mock out webpack for testing."""

    class FakeManifest(dict):
        def __getitem__(self, key):
            return f"/static/dist/{key}"

    from flask_webpackext.manifest import JinjaManifest

    monkeypatch.setattr(JinjaManifest, "load", lambda self, filepath: FakeManifest())

    # Disable checking for physical manifest file
    monkeypatch.setattr(
        "os.path.exists",
        lambda path: True if "manifest.json" in path else os.path.exists(path),
    )


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
