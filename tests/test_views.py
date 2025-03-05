"""Placeholder module for tests of view functions."""


def test_index_view(client, app):
    """Check that the Imperial index view renders without error."""
    res = app.test_client().get("https://localhost/")
    assert res.status_code == 200
    assert "Imperial College London" in res.data.decode("utf-8")
