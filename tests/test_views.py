"""Tests for the views."""

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from flask import render_template, render_template_string
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
    assert soup.find("a", href="/uploads/new?community=icl") is None
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
    notice_container = search_bar.find_next_sibling("div")
    notice = (
        notice_container.find("p", class_="header")
        if notice_container is not None
        else None
    )
    assert notice is None
    assert "You have read-only access." not in soup.get_text(" ", strip=True)

    # Check that the deposit button is visible.
    assert soup.find(id="quick-create-dropdown") is not None

    # Check depositor menus
    desktop_menu = soup.find(id="quick-create-menu")
    assert desktop_menu is not None
    upload_href = "/uploads/new?community=icl"
    assert desktop_menu.find("a", href=upload_href) is not None

    actions_heading = next(
        (h for h in soup.find_all("h2") if h.get_text(strip=True) == "Actions"),
        None,
    )
    assert actions_heading is not None
    mobile_menu = actions_heading.find_parent("div", class_="sub-menu")
    assert mobile_menu is not None
    assert mobile_menu.find("a", href=upload_href) is not None


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
