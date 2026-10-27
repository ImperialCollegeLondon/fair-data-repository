"""Tests for the views."""

import json

import pytest
from bs4 import BeautifulSoup
from ic_data_repo.permissions import deposit_action
from invenio_access.permissions import system_identity


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


def test_index_auth(user_client, app):
    """Check the index view with a logged in user."""
    res = user_client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    # Check that regular signed-users see the notice about read-only access.
    [notice] = soup.select("#frontpage-search-bar ~ div p.ui.header")
    assert "You have read-only access." in notice.get_text(" ", strip=True)
    [contact_link] = notice.select("a[href]")
    email = app.config["SUPPORT_CONTACT_EMAIL"]
    assert contact_link["href"] == f"mailto:{email}"
    assert contact_link.get_text(strip=True) == email
    assert soup.select("#quick-create-dropdown") == []
    assert soup.select("#quick-create-menu a[href='/uploads/new']") == []
    assert soup.select("div.sub-menu.mobile.tablet.only a[href='/uploads/new']") == []


def test_deposit_view_permissions(
    user, user_client, icl_community, vocabularies, app, permission_manager
):
    """Check that only users with deposit permissions can access the deposit page."""
    # permission denied initially
    response = user_client.get("/uploads/new")
    assert response.status_code == 403

    # grant access to the user
    permission_manager(deposit_action, user.id).grant()

    # page now accessible
    response = user_client.get("/uploads/new")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    for name, setting in (
        ("symplectic_search_enabled", "SYMPLECTIC_SEARCH_ENABLED"),
        ("data_deposit_agreement_url", "DATA_DEPOSIT_AGREEMENT_URL"),
    ):
        [field] = soup.select(f'main input[type="hidden"][name="{name}"]')
        assert json.loads(field["value"]) == app.config[setting]


def test_ui_changes_for_depositors(user_depositor, user_client):
    """Check customised front page menus for a depositor."""
    # As seen by depositors.
    res = user_client.get("/")
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, "html.parser")

    # Check that the depositors do not see the read-only access message
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


@pytest.mark.parametrize(
    ("entries", "has_description"),
    [
        ([("plain.csv", "L", "")], False),
        ([("described.csv", "D", "Definitions")], True),
        ([("plain.csv", "L", ""), ("described.csv", "D", "Definitions")], True),
        ([("described.csv", "D", "<strong>Text</strong>")], True),
        ([("described.csv", "D", "")], True),
    ],
)
def test_file_description_rendering(
    app,
    client,
    record_tester,
    files_tester,
    entries,
    has_description,
):
    """Render file descriptions through the record detail view."""
    # monkeypatch.setitem(app.config, "RDM_COMMUNITY_REQUIRED_TO_PUBLISH", False)
    record_tester.data["files"]["enabled"] = True
    draft = record_tester.create()

    for name, transfer_type, description in entries:
        transfer = {"type": transfer_type}

        if transfer_type == "D":
            transfer["description"] = description
        files_test = files_tester(draft.id, [{"key": name, "transfer": transfer}])
        files_test.init(system_identity)
        files_test.upload(system_identity)
        files_test.commit(system_identity)

    # publish with system identity to avoid needing a community
    record = record_tester.publish(identity=system_identity)

    response = client.get(f"/records/{record.id}")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")

    [table] = soup.select("#files-list-accordion-panel table.files")
    headers = [header.get_text(strip=True) for header in table.select("thead th")]
    assert ("Description" in headers) == has_description
    if has_description:
        assert headers[1] == "Description"

    rows = table.select("tbody > tr")
    assert len(rows) == len(entries)
    actual = {}
    for row in rows:
        cells = row.select(":scope > td")
        assert len(cells) == len(headers)
        [link] = cells[0].select("a")
        actual[link.get_text(strip=True)] = (
            cells[1].get_text(strip=True) if has_description else ""
        )
        if has_description:
            assert cells[1].select_one("strong") is None
    assert actual == {name: description for name, _, description in entries}
