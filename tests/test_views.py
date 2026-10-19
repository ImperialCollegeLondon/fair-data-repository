"""Tests for the views."""

import json

from bs4 import BeautifulSoup
from ic_data_repo.permissions import deposit_action
from invenio_access.permissions import ActionUsers, system_identity
from invenio_communities.proxies import current_communities


def test_index_view(client, app):
    """Simple check that index view does not give an error when rendered."""
    res = client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    [title] = soup.select("main .frontpage-hero h1")
    assert title.get_text(strip=True) == app.config["THEME_FRONTPAGE_TITLE"]

    [subtitle] = soup.select("main .frontpage-hero h2")
    assert subtitle.get_text(strip=True) == app.config["THEME_FRONTPAGE_SUBTITLE"]

    [search_records] = soup.select("main #frontpage-search-bar .search--label")
    assert search_records.get_text(strip=True) == "Search records"

    [page_footer] = soup.select("footer#rdm-footer-element")
    [contact] = page_footer.select("div.footer__contact")
    [brand] = contact.select("a.footer__brand")
    [brand_name] = brand.select("span[itemprop='name']")
    assert brand_name.get_text(strip=True) == "Imperial College London"

    [address] = contact.select("div.address")
    [street] = address.select("span[itemprop='streetAddress']")
    assert street.get_text(strip=True) == "South Kensington Campus"

    [footer_links] = page_footer.select("ul.footer__meta")
    links = footer_links.select("a[href]")
    assert any(
        link["href"] == f"mailto:{app.config['SUPPORT_CONTACT_EMAIL']}"
        for link in links
    )

    for setting in (
        "ACCESSIBILITY_STATEMENT_URL",
        "COOKIE_STATEMENT_URL",
        "POLICY_DOCUMENTS_URL",
        "USER_GUIDE_URL",
    ):
        assert any(link["href"] == app.config[setting] for link in links)


def test_index_auth(user_client):
    """Check the index view with a logged in user."""
    res = user_client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    [notice] = soup.select("#frontpage-search-bar ~ div p.ui.header")
    assert "You have read-only access." in notice.get_text(" ", strip=True)
    assert soup.select("#quick-create-dropdown") == []
    assert soup.select("#quick-create-menu a[href='/uploads/new']") == []
    assert soup.select("div.sub-menu.mobile.tablet.only a[href='/uploads/new']") == []


def test_deposit_view_permissions(user, user_client, db, location, vocabularies, app):
    """Check that only users with deposit permissions can access the deposit page."""
    # We need the icl community to exist first to test deposit permissions against.
    data = {
        "slug": "icl",
        "metadata": {
            "title": "Imperial College London",
            "description": "The Imperial College London community.",
        },
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
            "review_policy": "members",
        },
    }
    current_communities.service.create(system_identity, data)
    db.session.commit()

    # permission denied initially
    response = user_client.get("/uploads/new")
    assert response.status_code == 403

    # grant access to the user
    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))

    # page now accessible
    response = user_client.get("/uploads/new")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    symplectic = soup.select_one(
        'input[type="hidden"][name="symplectic_search_enabled"]'
    )
    assert symplectic is not None
    assert json.loads(symplectic["value"]) == app.config["SYMPLECTIC_SEARCH_ENABLED"]
    agreement = soup.select_one(
        'input[type="hidden"][name="data_deposit_agreement_url"]'
    )
    assert agreement is not None
    assert json.loads(agreement["value"]) == app.config["DATA_DEPOSIT_AGREEMENT_URL"]


def test_ui_changes_for_depositors(user, user_client, db):
    """Check customised front page menus for a depositor."""
    # As seen by depositors.
    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))

    res = user_client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    assert soup.select("#frontpage-search-bar ~ div p.ui.header") == []

    [dropdown] = soup.select("#quick-create-dropdown")
    [desktop_menu] = dropdown.select("#quick-create-menu[role='menu']")
    assert len(desktop_menu.select("a[role='menuitem'][href='/uploads/new']")) == 1

    assert (
        len(
            soup.select(
                "div.sub-menu.mobile.tablet.only "
                "a[role='menuitem'][href='/uploads/new']"
            )
        )
        == 1
    )
