"""Get information about a collection's record members in Invenio RDM."""

from flask import g
from flask_principal import Identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_records_resources.services.records.results import RecordItem


def get_collection_member_info(
    identity: Identity, record_id: str
) -> list[dict[str, str]]:
    """Get information about the member records for a given collection record ID.

    Args:
        identity: The identity of the user.
        record_id: The ID of the collection record.

    Returns:
        A list of dictionaries containing information about the member records.
    """
    record: RecordItem = records_service.read(identity, record_id)

    # Stop if there are no related identifiers.
    if "related_identifiers" not in record.data["metadata"]:
        return []

    member_dois = [
        rel["identifier"]
        for rel in record.data["metadata"]["related_identifiers"]
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


def template_collection_member_info(record_id: str) -> list[dict[str, str]]:
    """Get collection member information for the current user in templates.

    Args:
        record_id: The ID of the collection record.

    Returns:
        A list of dictionaries containing information about the member records.
    """
    return get_collection_member_info(g.identity, record_id)
