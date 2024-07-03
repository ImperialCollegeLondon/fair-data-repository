"""Implement OAuth handlers."""

from typing import Any

import jwt
import requests
from flask import current_app
from flask_oauthlib import OAuthRemote


def info_handler(
    remote_app: OAuthRemote, response_data: dict[str, Any]
) -> dict[str, Any]:
    """Extract account info from authorisation response.

    Extracts and validates the id_token returned as part of the OIDC workflow using
    metadata from the OpenId provider. Claims from the JWT are then returned in the
    expected structure for user sign-up process.

    Requires the following claims to be present in the id_token: email,
    preferred_username, name and oid.
    """
    oidc_config = requests.get(current_app.config["ICL_OAUTH_WELL_KNOWN_URL"]).json()
    signing_algos = oidc_config["id_token_signing_alg_values_supported"]
    jwks_client = jwt.PyJWKClient(oidc_config["jwks_uri"])

    id_token = response_data["id_token"]
    signing_key = jwks_client.get_signing_key_from_jwt(id_token)

    data = jwt.api_jwt.decode(
        id_token,
        key=signing_key.key,
        algorithms=signing_algos,
        audience=remote_app.consumer_key,
    )

    return dict(
        user=dict(
            email=data["email"],
            profile=dict(
                username=data["preferred_username"].rstrip("@ic.ac.uk"),
                full_name=data["name"],
            ),
        ),
        external_id=data["oid"],
        external_method="icl_sso",
        active=True,
    )
