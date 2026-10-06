"""Tests for the license restriction functionality."""

from contextlib import nullcontext

import pytest
from ic_data_repo.permissions import restricted_license_action
from invenio_access.permissions import ActionUsers
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records.models import RDMDraftMetadata
from invenio_records_resources.services.errors import PermissionDeniedError


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_restricted_license_permission_create(
    vocabularies,
    user_depositor,
    metadata,
    grant,
    outcome,
    db,
):
    """Test that restricted license permissions are enforced."""
    metadata["rights"] = [{"id": "cc-by-nd-4.0"}]
    if grant:
        db.session.add(
            ActionUsers.allow(restricted_license_action, user_id=user_depositor.id)
        )

    # Raises PermissionDeniedError if not granted permission.
    with outcome:
        current_rdm_records_service.create(
            user_depositor.identity,
            data={"metadata": metadata, "files": {"enabled": False}},
        )
    assert RDMDraftMetadata.query.count() == (1 if grant else 0)


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_restricted_license_permission_update(
    vocabularies,
    user_depositor,
    metadata,
    grant,
    outcome,
    db,
):
    """Test that restricted license permissions are enforced."""
    draft = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata, "files": {"enabled": False}},
    )
    assert draft["status"] == "draft_with_review"

    metadata["rights"] = [{"id": "cc-by-nd-4.0"}]
    if grant:
        db.session.add(
            ActionUsers.allow(restricted_license_action, user_id=user_depositor.id)
        )

    # Raises PermissionDeniedError if not granted permission.
    with outcome:
        current_rdm_records_service.update_draft(
            user_depositor.identity,
            draft.id,
            data={"metadata": metadata},
        )

    updated_draft = current_rdm_records_service.read_draft(
        user_depositor.identity,
        draft.id,
    )
    assert updated_draft["metadata"]["rights"][0]["id"] == (
        "cc-by-nd-4.0" if grant else "cc-by-4.0"
    )
