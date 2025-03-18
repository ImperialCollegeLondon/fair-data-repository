"""Placeholder module for tests of view functions."""

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


@pytest.fixture
def user_client(user, client):
    """A client logged in as the user fixture."""
    return user.login(client)


@pytest.fixture(scope="module")
def app_config(app_config):
    """Update invenio app_config fixture."""
    import json
    import os

    app_config["COLLECT_STORAGE"] = "flask_collect.storage.file"

    instance_path = app_config.get(
        "INSTANCE_PATH", os.environ.get("INVENIO_INSTANCE_PATH", "/tmp")
    )

    manifest_dir = os.path.join(instance_path, "static/dist")
    manifest_path = os.path.join(manifest_dir, "manifest.json")

    os.makedirs(manifest_dir, exist_ok=True)

    with open(manifest_path, "w") as f:
        json.dump({"entrypoints": {}, "chunks": {}}, f)

    app_config["WEBPACKEXT_MANIFEST_PATH"] = manifest_path

    return app_config


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
