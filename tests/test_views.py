"""Tests for the views."""

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

    main = soup.find("main", id="main")
    assert main is not None
    hero = main.find(class_="frontpage-hero")
    assert hero is not None
    title = hero.find("h1")
    assert title is not None
    assert title.get_text(strip=True) == app.config["THEME_FRONTPAGE_TITLE"]

    search_bar = soup.find(id="frontpage-search-bar")
    assert search_bar is not None
    form = search_bar.find("form", attrs={"role": "search"})
    assert form is not None
    assert form.find("input", attrs={"name": "q"}) is not None
    assert form.find("button", attrs={"type": "submit"}) is not None

    page_footer = soup.find("footer", id="rdm-footer-element")
    assert page_footer is not None
    footer = page_footer.find(class_="footer__meta")
    assert footer is not None
    assert (
        footer.find("a", href=f"mailto:{app.config['SUPPORT_CONTACT_EMAIL']}")
        is not None
    )

    for setting in (
        "ACCESSIBILITY_STATEMENT_URL",
        "COOKIE_STATEMENT_URL",
        "POLICY_DOCUMENTS_URL",
        "USER_GUIDE_URL",
    ):
        assert any(
            link.get("href") == app.config[setting]
            for link in footer.find_all("a", href=True)
        )


def test_index_auth(user_client):
    """Check the index view with a logged in user."""
    res = user_client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    search_bar = soup.find(id="frontpage-search-bar")
    assert search_bar is not None
    notice_container = search_bar.find_next_sibling("div")
    assert notice_container is not None
    notice = notice_container.find("p", class_="header")
    assert notice is not None
    assert "You have read-only access." in notice.get_text(" ", strip=True)
    assert soup.find(id="quick-create-dropdown") is None


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
    soup = BeautifulSoup(res.data, "html.parser")

    # Check that non-depositor information is shown.
    search_bar = soup.find(id="frontpage-search-bar")
    assert search_bar is not None
    notice_container = search_bar.find_next_sibling("div")
    assert notice_container is not None
    notice = notice_container.find("p", class_="header")
    assert notice is not None
    assert "You have read-only access." in notice.get_text(" ", strip=True)
    # Check that the deposit button is not visible.
    assert soup.find(id="quick-create-dropdown") is None

    # As seen by depositors.
    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))
    res = user_client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    # Check that non-depositor information is not shown.
    search_bar = soup.find(id="frontpage-search-bar")
    assert search_bar is not None
    assert search_bar.find_next_sibling("div") is None
    assert "You have read-only access." not in soup.get_text(" ", strip=True)

    # Check that the deposit button is visible.
    assert soup.find(id="quick-create-dropdown") is not None
