"""Tests for the link-only ORCID OAuth integration."""

import runpy
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from invenio_oauthclient.models import RemoteAccount, RemoteToken
from invenio_oauthclient.proxies import current_oauthclient


@pytest.fixture(scope="module")
def app_config(app_config):
    """Register a link-only ORCID remote app for this test module."""
    from invenio_oauthclient.contrib.orcid import ORCIDOAuthSettingsHelper

    orcid_app = ORCIDOAuthSettingsHelper(
        title="ORCID", description="Link your Helix account to your ORCID iD."
    ).remote_app
    orcid_app["hide"] = True

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


def test_orcid_hidden_from_linked_accounts_page(user_client):
    """ORCID is not listed as linkable on the standard linked-accounts page."""
    resp = user_client.get("/account/settings/linkedaccounts/")
    assert resp.status_code == 200
    assert b"ORCID" not in resp.data


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

    start_resp = user_client.get("/account/settings/orcid/connect")
    assert start_resp.status_code == 302

    query = parse_qs(urlparse(start_resp.headers["Location"]).query)
    state = query["state"][0]

    remote = current_oauthclient.oauth.remote_apps["orcid"]

    with patch.object(remote, "handle_oauth2_response", return_value=fake_response):
        callback_resp = user_client.get(
            f"/oauth/authorized/orcid/?state={state}&code=fake-code"
        )

    assert callback_resp.status_code in (302, 200)

    account = RemoteAccount.get(user_id=user.id, client_id=remote.consumer_key)
    assert account is not None
    assert account.extra_data.get("orcid") == orcid_id
    assert account.extra_data.get("full_name") == "Ada Lovelace"

    token = RemoteToken.get(user_id=user.id, client_id=remote.consumer_key)
    assert token is not None
    assert token.access_token == fake_response["access_token"]
