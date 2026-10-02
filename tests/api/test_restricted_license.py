"""Tests for the license restriction functionality."""

import pytest
from ic_data_repo.permissions import restricted_license_action
from invenio_access.permissions import ActionUsers
from invenio_rdm_records.records.models import RDMDraftMetadata


@pytest.mark.parametrize("grant", [True, False])
def test_restricted_license_permission_create(
    grant,
    user_client,
    location,
    vocabularies,
    user_depositor,
    api_headers,
    metadata,
    db,
):
    """Test that restricted license permissions are enforced."""
    metadata["rights"] = [{"id": "cc-by-nd-4.0"}]
    if grant:
        db.session.add(
            ActionUsers.allow(restricted_license_action, user_id=user_depositor.id)
        )

    result = user_client.post(
        "/records",
        json={
            "metadata": metadata,
            "files": {"enabled": False},
        },
        headers=api_headers,
    )
    assert result.status_code == (201 if grant else 403)

    assert RDMDraftMetadata.query.count() == (1 if grant else 0)


@pytest.mark.parametrize("grant", [True, False])
def test_restricted_license_permission_update(
    grant,
    user_client,
    location,
    vocabularies,
    user_depositor,
    api_headers,
    metadata,
    db,
):
    """Test that restricted license permissions are enforced."""
    result = user_client.post(
        "/records",
        json={
            "metadata": metadata,
            "files": {"enabled": False},
        },
        headers=api_headers,
    )
    assert result.status_code == 201
    draft_id = result.json["id"]

    metadata["rights"] = [{"id": "cc-by-nd-4.0"}]
    if grant:
        db.session.add(
            ActionUsers.allow(restricted_license_action, user_id=user_depositor.id)
        )

    result = user_client.put(
        f"/records/{draft_id}/draft",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == (200 if grant else 403)

    result = user_client.get(
        f"/records/{draft_id}/draft",
        headers=api_headers,
    )
    assert result.status_code == 200

    assert result.json["metadata"]["rights"][0]["id"] == (
        "cc-by-nd-4.0" if grant else "cc-by-4.0"
    )
