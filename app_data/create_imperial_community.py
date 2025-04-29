"""Script to create_app Imperial Community."""

from invenio_access.permissions import system_identity
from invenio_app.factory import create_app
from invenio_communities.proxies import current_communities


def create_community():
    """Create the community."""
    current_communities.service.create(
        data=dict(
            slug="icl",
            metadata=dict(title="Imperial College London"),
            access=dict(visibility="public"),
        ),
        identity=system_identity,
    )


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_community()
