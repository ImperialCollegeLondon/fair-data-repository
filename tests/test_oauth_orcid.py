"""Tests for the link-only ORCID OAuth integration."""

import runpy
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from flask import url_for
from ic_data_repo.auth.orcid import authorized_handler
from invenio_accounts.models import UserIdentity
from invenio_oauthclient.models import RemoteAccount, RemoteToken
from invenio_oauthclient.proxies import current_oauthclient

LINKED_ACCOUNTS_URL = "/account/settings/linkedaccounts/"


@pytest.fixture(scope="module")
def app_config(app_config):
    """Register a link-only ORCID remote app for this test module."""
    from invenio_oauthclient.contrib.orcid import ORCIDOAuthSettingsHelper

    orcid_app = ORCIDOAuthSettingsHelper(
        title="ORCID", description="Link your Helix account to your ORCID iD."
    ).remote_app
    orcid_app["hide"] = True
    orcid_app["authorized_handler"] = "ic_data_repo.auth.orcid:authorized_handler"

    app_config["OAUTHCLIENT_REMOTE_APPS"]["orcid"] = orcid_app
    app_config["ORCID_OAUTH_ENABLED"] = True
    app_config["ORCID_APP_CREDENTIALS"] = {
        "consumer_key": "test-orcid-client-id",
        "consumer_secret": "test-orcid-client-secret",
    }
    return app_config


def _settings_for_credentials(monkeypatch, client_id, client_secret):
    """Execute ``ic_data_repo.config.settings`` with the given env vars."""
    for key, value in (
        ("ORCID_OAUTH_CLIENT_ID", client_id),
        ("ORCID_OAUTH_CLIENT_SECRET", client_secret),
    ):
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)

    return runpy.run_module(
        "ic_data_repo.config.settings", run_name="ic_data_repo_settings_reload"
    )


def test_orcid_enabled_and_link_only(monkeypatch):
    """With both credentials set, the remote app registers as hidden."""
    settings = _settings_for_credentials(monkeypatch, "test-id", "test-secret")

    assert settings["ORCID_OAUTH_ENABLED"] is True
    orcid_app = settings["OAUTHCLIENT_REMOTE_APPS"]["orcid"]
    assert orcid_app["hide"] is True
    assert (
        orcid_app["authorized_handler"] == "ic_data_repo.auth.orcid:authorized_handler"
    )

    params = orcid_app["params"]
    assert params["authorize_url"] == "https://orcid.org/oauth/authorize"
    assert params["access_token_url"] == "https://orcid.org/oauth/token"

    assert settings["ORCID_APP_CREDENTIALS"] == {
        "consumer_key": "test-id",
        "consumer_secret": "test-secret",
    }


def test_orcid_hidden_from_login_route(app, client):
    """The standard oauthclient login route 404s for the hidden ORCID app."""
    resp = client.get("/oauth/login/orcid/")
    assert resp.status_code == 404


def _start_link(user_client):
    """Start the ORCID link flow and return the OAuth state token."""
    resp = user_client.get("/account/settings/orcid/connect")
    assert resp.status_code == 302
    return parse_qs(urlparse(resp.headers["Location"]).query)["state"][0]


def test_linked_accounts_unlinked(user_client):
    """An unlinked user sees a Link ORCID action using the connect route."""
    resp = user_client.get(LINKED_ACCOUNTS_URL)
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "Link ORCID" in html
    assert 'href="/account/settings/orcid/connect"' in html
    # ORCID is never offered via the generic login or disconnect routes
    assert "/oauth/login/orcid" not in html
    assert "/oauth/disconnect/orcid" not in html


def test_linked_accounts_linked(db, user, user_client):
    """A linked user sees their ORCID iD and no link or disconnect action."""
    orcid_id = "0000-0002-1825-0097"
    UserIdentity.create(user.user, "orcid", orcid_id)
    db.session.commit()

    resp = user_client.get(LINKED_ACCOUNTS_URL)
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "Link ORCID" not in html
    assert f"https://orcid.org/{orcid_id}" in html
    assert "/oauth/disconnect/orcid" not in html


def test_linked_accounts_unavailable(app, user_client):
    """No Link ORCID action is shown when ORCID is not configured."""
    with patch.dict(app.config, {"ORCID_OAUTH_ENABLED": False}):
        resp = user_client.get(LINKED_ACCOUNTS_URL)
    assert resp.status_code == 200
    assert b"Link ORCID" not in resp.data


def test_settings_menu(user_client):
    """Linked Accounts is in the settings menu; Applications stays hidden."""
    resp = user_client.get(LINKED_ACCOUNTS_URL)
    html = resp.data.decode("utf-8")
    assert 'href="/account/settings/linkedaccounts/"' in html
    assert 'href="/account/settings/applications/"' not in html


def test_connect_requires_login(client):
    """Anonymous users are redirected to log in, not sent to ORCID."""
    resp = client.get("/account/settings/orcid/connect")
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_connect_404_when_unconfigured(app, user_client):
    """The connect route 404s if ORCID_OAUTH_ENABLED is false."""
    with patch.dict(app.config, {"ORCID_OAUTH_ENABLED": False}):
        resp = user_client.get("/account/settings/orcid/connect")
    assert resp.status_code == 404


def test_connect_redirects_to_orcid(user_client):
    """A logged-in user is sent straight to ORCID's authorize endpoint."""
    resp = user_client.get("/account/settings/orcid/connect")
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("https://orcid.org/oauth/authorize")


def test_link_orcid_account(app, db, user, user_client):
    """Completing the OAuth dance links ORCID to the already-logged-in user."""
    orcid_id = "0000-0002-1825-0097"
    fake_response = {
        "access_token": "fake-access-token",
        "token_type": "bearer",
        "orcid": orcid_id,
        "name": "Ada Lovelace",
    }

    state = _start_link(user_client)
    remote = current_oauthclient.oauth.remote_apps["orcid"]

    with patch.object(remote, "handle_oauth2_response", return_value=fake_response):
        callback_resp = user_client.get(
            f"/oauth/authorized/orcid/?state={state}&code=fake-code"
        )

    assert callback_resp.status_code == 302
    assert urlparse(callback_resp.headers["Location"]).path == LINKED_ACCOUNTS_URL

    account = RemoteAccount.get(user_id=user.id, client_id=remote.consumer_key)
    assert account is not None
    assert account.extra_data.get("orcid") == orcid_id
    assert account.extra_data.get("full_name") == "Ada Lovelace"

    token = RemoteToken.get(user_id=user.id, client_id=remote.consumer_key)
    assert token is not None
    assert token.access_token == fake_response["access_token"]

    identity = UserIdentity.query.filter_by(id_user=user.id, method="orcid").one()
    assert identity.id == orcid_id


def test_link_orcid_refused(user, user_client):
    """Refusing on ORCID returns to Linked Accounts without linking."""
    state = _start_link(user_client)

    resp = user_client.get(
        f"/oauth/authorized/orcid/?state={state}&error=access_denied"
    )
    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == LINKED_ACCOUNTS_URL

    assert UserIdentity.query.filter_by(id_user=user.id, method="orcid").count() == 0


def test_link_orcid_invalid_state(user, user_client):
    """A callback with a tampered state is rejected without linking."""
    _start_link(user_client)

    resp = user_client.get("/oauth/authorized/orcid/?state=invalid&code=fake-code")
    assert resp.status_code == 403

    assert UserIdentity.query.filter_by(id_user=user.id, method="orcid").count() == 0


def test_authorized_handler_requires_login(app):
    """The ORCID callback handler never signs in or registers anonymous users."""
    remote = current_oauthclient.oauth.remote_apps["orcid"]
    with app.test_request_context("/oauth/authorized/orcid/"):
        with patch("ic_data_repo.auth.orcid._authorized") as base_handler:
            resp = authorized_handler({"access_token": "token"}, remote)
            login_url = url_for("security.login")

    base_handler.assert_not_called()
    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == login_url
