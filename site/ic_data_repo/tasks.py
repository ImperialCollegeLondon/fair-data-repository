"""Tasks to be run by celery.

In particular, this includes tasks to be run periodically in the background.
"""

from celery import shared_task
from flask import current_app

from .microsoft_graph_api_client import get_client
from .vocabs import import_imperial_contributors_to_invenio


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
