"""Utilities for settings."""

from typing import Any

from flask_login import current_user
from invenio_accounts.models import UserIdentity

_ICL_ROR_ID = "041kmwe10"
"""The ROR identifier for Imperial."""


def _get_user_orcid() -> str | None:
    """Return the ORCID iD the current user has linked, if any."""
    identity = UserIdentity.query.filter_by(
        id_user=current_user.id, method="orcid"
    ).first()
    return identity.id if identity else None


def get_user_form_default() -> list[dict[str, Any]]:
    """Format the current user profile for the submission form.

    The default user profile schema has two string properties;
    full name and affiliations.
    https://github.com/inveniosoftware/invenio-accounts/blob/master/invenio_accounts/profiles/schemas.py

    If the user has linked their ORCID account, its iD is added as an identifier.
    """
    try:
        name = current_user.user_profile["full_name"]
        given_name = name.split(", ")[1]
        family_name = name.split(", ")[0]
    except KeyError:
        return []

    affiliations = []
    if profile_affiliations := current_user.user_profile.get("affiliations"):
        if profile_affiliations == "Imperial College London":
            affiliations.append({"id": _ICL_ROR_ID})
        else:
            affiliations.append({"name": current_user.user_profile["affiliations"]})

    person_or_org: dict[str, Any] = {
        "type": "personal",
        "name": name,
        "given_name": given_name,
        "family_name": family_name,
    }
    if orcid := _get_user_orcid():
        person_or_org["identifiers"] = [{"scheme": "orcid", "identifier": orcid}]

    return [
        {
            "person_or_org": person_or_org,
            "affiliations": affiliations,
        },
    ]
