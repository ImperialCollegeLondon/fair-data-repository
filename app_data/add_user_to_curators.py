"""Script to add a user to the Imperial community curators."""

import argparse

from invenio_access.permissions import system_identity
from invenio_accounts.models import User
from invenio_app.factory import create_app
from invenio_communities.proxies import current_communities


def add_curator(email: str) -> None:
    """Add a user to the Imperial community curators."""
    user = User.query.filter_by(email=email).one()
    community = current_communities.service.read(system_identity, "icl")

    current_communities.service.members.add(
        system_identity,
        community.id,
        {
            "role": "curator",
            "members": [
                {"type": "user", "id": str(user.id)},
            ],
            "visible": True,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add a user to the Imperial community curators."
    )
    parser.add_argument("email", help="The email of the user to add to the curators.")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        add_curator(args.email)
