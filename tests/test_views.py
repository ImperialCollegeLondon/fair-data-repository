"""Tests for the views."""

import re
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from ic_data_repo.permissions import deposit_action
from invenio_access.permissions import ActionUsers


@pytest.fixture(autouse=True)
def mock_manifest():
    """Mock manifest to always return a value for theme.css."""
    with patch("flask_webpackext.manifest.JinjaManifest.__getitem__") as mock:
        mock.return_value = '<link rel="stylesheet" href="/static/dist/theme.css">'
        yield mock


def test_index_view(client, app):
    """Simple check that index view does not give an error when rendered."""
    res = client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    hero = soup.select_one("main#main .frontpage-hero")
    assert hero is not None
    assert (
        hero.select_one("h1").get_text(strip=True)
        == app.config["THEME_FRONTPAGE_TITLE"]
    )

    form = soup.select_one("#frontpage-search-bar form[role='search']")
    assert form is not None
    assert form.select_one("input[name='q']") is not None
    assert form.select_one("button[type='submit']") is not None

    footer = soup.select_one("footer#rdm-footer-element .footer__meta")
    assert footer is not None
    assert (
        footer.select_one(f"a[href='mailto:{app.config['SUPPORT_CONTACT_EMAIL']}']")
        is not None
    )
    for setting in (
        "ACCESSIBILITY_STATEMENT_URL",
        "COOKIE_STATEMENT_URL",
        "POLICY_DOCUMENTS_URL",
        "USER_GUIDE_URL",
    ):
        assert any(
            link.get("href") == app.config[setting] for link in footer.select("a[href]")
        )


def test_index_auth(user_client):
    """Check the index view with a logged in user."""
    res = user_client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    notice = soup.select_one("#frontpage-search-bar ~ div p.ui.header")
    assert notice is not None
    assert "You have read-only access." in notice.get_text(" ", strip=True)
    assert soup.select_one("#quick-create-dropdown") is None


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
