"""Tasks to be run by celery.

In particular, this includes tasks to be run periodically in the background.
"""

from io import BytesIO

import requests
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity

from .microsoft_graph_api_client import get_client
from .vocabs import import_imperial_contributors_to_invenio, import_to_vocabulary


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
            {"type": "json"},
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
