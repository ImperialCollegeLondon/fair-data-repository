"""Utilities for settings."""

from typing import Any, List

from flask_login import current_user


def get_user_form_default() -> List[dict[str, Any]]:
    """Format the current user profile for the submission form.

    The default user profile schema has two string properties;
    full name and affiliations. More details (identifiers?) would
    have to come from the SSO.
    https://github.com/inveniosoftware/invenio-accounts/blob/master/invenio_accounts/profiles/schemas.py
    """
    affiliations = []

    try:
        name = current_user.user_profile["full_name"]
        given_name = name.split(", ")[1]
        family_name = name.split(", ")[0]
    except KeyError:
        return []

    if "affiliations" in current_user.user_profile:
        affiliations.append({"name": current_user.user_profile["affiliations"]})

    return [
        {
            "person_or_org": {
                "type": "personal",
                "name": name,
                "given_name": given_name,
                "family_name": family_name,
            },
            "affiliations": affiliations,
        },
    ]
