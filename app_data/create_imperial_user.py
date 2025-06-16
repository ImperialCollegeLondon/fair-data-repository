"""Script to automatically create an Invenio user from Imperial."""

import argparse
import asyncio
from datetime import datetime

from ic_data_repo.microsoft_graph_api_client import get_client
from invenio_app.factory import create_app


def add_user(username, app):
    """Create a new Invenio user."""
    datastore = app.extensions["security"].datastore

    client = get_client(
        app.config["ICL_MICROSOFT_TENANT_ID"],
        app.config["ICL_OAUTH_CLIENT_ID"],
        app.config["ICL_OAUTH_CLIENT_SECRET"],
    )
    user = asyncio.run(client.users.by_user_id(f"{username}@ic.ac.uk").get())
    datastore.create_user(
        username=username,
        email=user.mail,
        active=True,
        confirmed_at=datetime.utcnow(),
        user_profile=dict(
            affiliations="Imperial College London", full_name=user.display_name
        ),
    )
    datastore.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a new user from Imperial identity data."
    )
    parser.add_argument("username", help="The user to add.")
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        add_user(args.username, app)
