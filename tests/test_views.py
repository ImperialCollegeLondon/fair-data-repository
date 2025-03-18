"""Placeholder module for tests of view functions."""

import re

import pytest
import os


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


def test_index_view(client):
    """Simple check that index view does not give an error when rendered."""
    if os.environ.get('CI'):
        pytest.skip("Skipping in CI environment due to missing webpack assets")
    
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
