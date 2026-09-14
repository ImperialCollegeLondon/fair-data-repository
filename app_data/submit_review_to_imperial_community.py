"""Script to submit a record for review to the Imperial community.

This script is provided as a workaround for
https://github.com/ImperialCollegeLondon/fair-data-repository/issues/329
drafts that get disassociated from the imperial community can be manually
submitted for review.
"""

import argparse

from invenio_access.permissions import system_identity
from invenio_access.utils import get_identity
from invenio_accounts.proxies import current_datastore as current_accounts_datastore
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

    # get user identity so we can use it to create the review request
    user = current_accounts_datastore.get_user(user_id)
    user_identity = get_identity(user)

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
