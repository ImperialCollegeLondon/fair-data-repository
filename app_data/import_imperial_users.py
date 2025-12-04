"""A script to import Imperial users into the Invenio names vocabulary."""

import os
import sys

from ic_data_repo.microsoft_graph_api_client import get_client
from ic_data_repo.vocabs import import_imperial_contributors_to_invenio

if __name__ == "__main__":
    client_id = os.getenv("ICL_OAUTH_CLIENT_ID")
    client_secret = os.getenv("ICL_OAUTH_CLIENT_SECRET")
    tenant_id = "2b897507-ee8c-4575-830b-4f8267c3d307"
    if not client_id or not client_secret:
        raise RuntimeError(
            "ICL_OAUTH_CLIENT_ID and ICL_OAUTH_CLIENT secret env vars must be set"
        )
    client = get_client(tenant_id, client_id, client_secret)

    # Let user specify max number of users to retrieve so they can things without
    # loading the lot
    max_count = int(sys.argv[1]) if len(sys.argv) > 1 else None
    import_imperial_contributors_to_invenio(client, max_count=max_count)
