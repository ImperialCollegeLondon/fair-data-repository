"""Tasks to be run by celery.

In particular, this includes tasks to be run periodically in the background.
"""

from celery import shared_task
from flask import current_app
from ic_data_repo.config import (
    ICL_MICROSOFT_TENANT_ID,
    ICL_OAUTH_CLIENT_ID,
    ICL_OAUTH_CLIENT_SECRET,
)
from ic_data_repo.microsoft_graph_api_client import get_client
from ic_data_repo.vocabs import import_imperial_contributors_to_invenio


@shared_task
def update_imperial_users() -> None:
    """Update the list of possible contributors from Imperial."""
    if not ICL_OAUTH_CLIENT_ID or not ICL_OAUTH_CLIENT_SECRET:
        raise RuntimeError(
            "ICL_OAUTH_CLIENT_ID and ICL_OAUTH_CLIENT_SECRET env vars must be set"
        )

    client = get_client(
        ICL_MICROSOFT_TENANT_ID, ICL_OAUTH_CLIENT_ID, ICL_OAUTH_CLIENT_SECRET
    )
    import_imperial_contributors_to_invenio(client, current_app.logger)
