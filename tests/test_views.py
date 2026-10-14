"""Tests for the views."""

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from flask import render_template, render_template_string
from ic_data_repo.permissions import deposit_action
from invenio_access.permissions import ActionUsers, system_identity
from invenio_communities.proxies import current_communities


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
    symplectic = soup.find(
        "input",
        attrs={"type": "hidden", "name": "symplectic_search_enabled"},
    )
    assert symplectic is not None
    assert json.loads(symplectic["value"]) == app.config["SYMPLECTIC_SEARCH_ENABLED"]
    agreement = soup.find(
        "input",
        attrs={"type": "hidden", "name": "data_deposit_agreement_url"},
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


@pytest.mark.parametrize(
    ("entries", "has_description"),
    [
        ([], False),
        ([("plain.csv", "L", "", False)], False),
        ([("described.csv", "D", "Column definitions", False)], True),
        (
            [
                ("plain.csv", "L", "", False),
                ("described.csv", "D", "Column definitions", False),
            ],
            True,
        ),
        ([("described.csv", "D", "<strong>Text</strong>", False)], True),
        (
            [
                ("plain.csv", "L", "", False),
                ("hidden.csv", "D", "Hidden description", True),
            ],
            True,
        ),
    ],
)
def test_file_description_rendering(app, entries, has_description):
    """Check description columns, row alignment and escaping."""
    files = [
        {
            "key": name,
            "size": 1024,
            "checksum": "sha256:test",
            "access": {"hidden": hidden},
            "transfer": {"type": transfer, "description": description},
        }
        for name, transfer, description, hidden in entries
    ]
    with app.test_request_context():
        markup = render_template_string(
            """
            {% from "invenio_app_rdm/records/macros/files.html"
               import file_list with context %}
            {{ file_list(files, "record-1", false, false,
                         record=record, with_preview=false) }}
            """,
            files=files,
            record={"ui": {"access_status": {"id": "open"}}},
            transfer_types={"REMOTE": "R"},
            config={
                "RDM_ARCHIVE_DOWNLOAD_ENABLED": False,
                "APP_RDM_DISPLAY_DECIMAL_FILE_SIZES": False,
            },
        )
    table = BeautifulSoup(markup, "html.parser").find("table", class_="files")
    assert table is not None
    headers = table.find("thead").find_all("th")
    expected = (
        ["Name", "Description", "Size", ""] if has_description else ["Name", "Size", ""]
    )
    assert [header.get_text(strip=True) for header in headers] == expected
    rows = table.find("tbody").find_all("tr")
    visible = [file for file in files if not file["access"]["hidden"]]
    assert len(rows) == len(visible)
    for row, file in zip(rows, visible, strict=True):
        cells = row.find_all("td", recursive=False)
        assert len(cells) == len(headers)
        assert cells[0].find("a").get_text(strip=True) == file["key"]
        if has_description:
            assert cells[1].get_text(strip=True) == file["transfer"]["description"]
            assert cells[1].find("strong") is None


@pytest.mark.parametrize("description", [None, "<p>Dataset summary</p>"])
def test_record_description_rendering(app, description):
    """Check record description rendering."""
    record = SimpleNamespace(ui=SimpleNamespace(additional_descriptions=[]))
    with app.test_request_context():
        markup = render_template(
            "invenio_app_rdm/records/details/description.html",
            metadata={"description": description},
            record=record,
        )

    section = BeautifulSoup(markup, "html.parser").find("section", id="description")
    assert (section is not None) == bool(description)
    if section is not None:
        content = section.find("div", style=True)
        assert content is not None
        assert "white-space: pre-wrap" in content["style"]
        assert "word-wrap: break-word" in content["style"]
        assert content.find("p").get_text(strip=True) == "Dataset summary"
