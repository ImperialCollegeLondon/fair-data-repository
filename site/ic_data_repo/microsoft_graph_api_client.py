"""Client interface for the Microsoft Graph API."""

from typing import Any, Optional

import requests
from flask import current_app


def _get_app_access_token() -> str:
    """Get an access token for the application to use the Microsoft Graph API.

    Fetches an access token that is enabled for app-only access i.e. not on behalf of a
    logged in user.
    """
    tenant_id = current_app.config["ICL_OAUTH_WELL_KNOWN_URL"].split("/")[3]
    response = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "grant_type": "client_credentials",
            "client_id": current_app.config["ICL_OAUTH_CLIENT_ID"],
            "client_secret": current_app.config["ICL_OAUTH_CLIENT_SECRET"],
            "scope": "https://graph.microsoft.com/.default",
        },
    )
    return response.json()["access_token"]


def get_user_info(username: str, access_token: Optional[str] = None) -> dict[str, Any]:
    """Get user profile information from the Microsoft Graph API."""
    if access_token is None:
        access_token = _get_app_access_token()

    response = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{username}@ic.ac.uk",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()
