"""Tasks to be run by celery.

In particular, this includes tasks to be run periodically in the background.
"""

from io import BytesIO
from pathlib import Path

import requests
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity

from .microsoft_graph_api_client import get_client
from .symplectic_interface import SymplecticClient
from .vocabs import import_imperial_contributors_to_invenio, import_to_vocabulary

# Define a mapping for relation_type to type_id more can be added as needed
relation_type_to_type_id = {
    "isderivedfrom": 1,
    "issupplementedby": 131,
}


@shared_task
def update_imperial_users() -> None:
    """Update the list of possible contributors from Imperial."""
    if not current_app.config["ICL_GRAPH_API_ENABLED"]:
        return

    client = get_client(
        current_app.config["ICL_MICROSOFT_TENANT_ID"],
        current_app.config["ICL_OAUTH_CLIENT_ID"],
        current_app.config["ICL_OAUTH_CLIENT_SECRET"],
    )
    import_imperial_contributors_to_invenio(client, current_app.logger)


@shared_task
def update_funders_vocabulary(archive_download_url: str) -> None:
    """Update the funder vocabulary from the ROR data dump."""
    # download the data zip archive
    response = requests.get(archive_download_url)
    response.raise_for_status()

    datastream_config = {
        "readers": [
            {
                "type": "zip",
                "args": {
                    "origin": BytesIO(response.content),
                    "regex": r"-ror-data\.json",
                },
            },
            # exploiting that yaml is a json superset use our streaming reader
            # helps avoid memory issues in deployment
            {"type": "stream-yaml"},
        ],
        "transformers": [{"type": "ror-funder"}],
        "writers": [
            {
                "type": "funders-service",
                "args": {"identity": system_identity, "update": True},
            }
        ],
    }
    import_to_vocabulary(datastream_config, allow_errors=False)


@shared_task
def export_record_to_symplectic(record) -> None:
    """Syncronise record metadata to symplectic."""
    if not current_app.config["SYMPLECTIC_ENABLED"]:
        return

    client = SymplecticClient(
        current_app.config["SYMPLECTIC_API_URL"],
        current_app.config["SYMPLECTIC_API_SUBSCRIPTION_KEY"],
    )
    object_id = client.create_record(record, current_app.config["DATACITE_PREFIX"])

    metadata = record.get("metadata", {})
    related_identifiers = metadata.get("related_identifiers", [])

    related_work_doi = {
        identifier["identifier"]: type_id
        for identifier in related_identifiers
        if identifier.get("scheme") == "doi"
        and (relation_type := identifier.get("relation_type", {})).get("id")
        and (type_id := relation_type_to_type_id.get(relation_type["id"])) is not None
    }

    for doi, type_id in related_work_doi.items():
        related_object_ids = client.fetch_related_objects(doi)
        for related_object_id in related_object_ids:
            client.link_related_records(
                object_id, related_object_id, type_id, to_object_type="publication"
            )

    funding = metadata.get("funding", [])

    for fund in funding:
        award = fund.get("award", {})
        if award_id := award.get("id"):
            award_id_type = "institution-reference"
        elif award_id := award.get("number"):
            award_id_type = "funder-reference"

        if award_id:
            try:
                related_award_id = client.get_related_awards(award_id, award_id_type)
                client.link_related_records(
                    object_id, related_award_id, type_id=2, to_object_type="grant"
                )
            except ValueError as e:
                # Log the error but continue processing other awards
                current_app.logger.exception(f"Failed to link award {award_id}: {e}")
                continue

    return


@shared_task
def import_full_affilations_vocab():
    """Import the full affiliations vocabulary from YAML file in app_data."""
    datastream_config = {
        "readers": [
            {
                "type": "stream-yaml",
                "args": {
                    "origin": Path(current_app.instance_path)
                    / "app_data"
                    / "vocabularies"
                    / "affiliations_ror_full.yaml",
                },
            },
        ],
        "transformers": [],
        "writers": [
            {
                "type": "affiliations-service",
                "args": {"identity": system_identity, "update": True},
            }
        ],
    }
    import_to_vocabulary(datastream_config, allow_errors=False)
