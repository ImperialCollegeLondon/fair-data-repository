"""Get information about a collection's record members in Invenio RDM."""

from typing import Any

from flask import g
from flask_principal import Identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service


def get_collection_member_info(
    identity: Identity, related: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """Get information about the member records for a given collection record.

    Args:
        identity: Identity of the user.
        related: Related identifiers dict from the collection's metadata.

    Returns:
        A list of dictionaries containing information about the member records.
    """
    member_dois = [
        rel["identifier"]
        for rel in related
        if rel["relation_type"]["id"] == "haspart" and rel["scheme"] == "doi"
    ]

    # Stop if none of the relations have id=haspart and scheme=doi.
    if not member_dois:
        return []

    # Search published records.
    q = " OR ".join(
        f'parent.pids.doi.identifier.keyword:"{doi}"' for doi in member_dois
    )
    members = records_service.scan(identity, params={"q": q})

    return [
        {
            "doi": member["parent"]["pids"]["doi"]["identifier"],
            "url": member["links"]["self_html"],
            "title": member["metadata"]["title"],
        }
        for member in members
    ]


def template_collection_member_info(
    related: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Get collection member information for the current user in templates.

    Args:
        related: Related identifiers dict from the collection's metadata.

    Returns:
        A list of dictionaries containing information about the member records.
    """
    return get_collection_member_info(g.identity, related)
