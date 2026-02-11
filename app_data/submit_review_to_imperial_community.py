"""Script to submit a record for review to the Imperial community.

This script is provided as a workaround for
https://github.com/ImperialCollegeLondon/fair-data-repository/issues/329
drafts that get disassociated from the imperial community can be manually
submitted for review.
"""

import argparse

from flask_principal import Identity, UserNeed
from invenio_access.permissions import any_user, authenticated_user, system_identity
from invenio_app.factory import create_app
from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_rdm_records_service


def submit_for_review(record_id: str) -> None:
    """Submit a record for review to the Imperial community."""
    icl_community = next(
        current_communities.service.search(
            identity=system_identity, params=dict(q="slug:icl")
        ).hits
    )
    draft = current_rdm_records_service.read_draft(system_identity, record_id)

    # looking up the record owner as below looks a bit hacky but seems to be expected
    # method used in the invenio_rdm_records codebase.
    user_id = int(draft.data["parent"]["access"]["owned_by"]["user"])

    # create identity with required permissions so we can submit the record as the user
    # who owns it
    user_identity = Identity(user_id)
    user_identity.provides.add(UserNeed(user_id))
    user_identity.provides.add(any_user)
    user_identity.provides.add(authenticated_user)

    # create and submit the review request
    current_rdm_records_service.review.update(
        user_identity,
        record_id,
        dict(receiver=dict(community=icl_community["id"]), type="community-submission"),
    )
    current_rdm_records_service.review.submit(
        user_identity,
        record_id,
        dict(),
        require_review=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Submit a record for review to the Imperial community."
    )
    parser.add_argument("record_id", help="The id of the record to submit for review.")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        submit_for_review(args.record_id)
