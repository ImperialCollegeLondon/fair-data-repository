"""Tests for the license restriction functionality."""

from contextlib import nullcontext

import pytest
from ic_data_repo.permissions import restricted_license_action
from invenio_rdm_records.records.models import RDMDraftMetadata
from invenio_records_resources.services.errors import PermissionDeniedError


@pytest.fixture
def restricted_license_permission(permission_manager):
    """Fixture for restricted license permission."""
    return permission_manager(restricted_license_action)


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_restricted_license_permission_create(
    restricted_license_permission, record_tester, grant, outcome
):
    """Test that restricted license permissions are enforced."""
    record_test = record_tester()
    record_test.data["metadata"]["rights"] = [{"id": "cc-by-nd-4.0"}]

    if grant:
        restricted_license_permission.grant()

    # Raises PermissionDeniedError if not granted permission.
    with outcome:
        record_test.create()
    assert RDMDraftMetadata.query.count() == (1 if grant else 0)


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_restricted_license_permission_update(
    restricted_license_permission, record_tester, grant, outcome
):
    """Test that restricted license permissions are enforced."""
    record_test = record_tester()
    record_test.create()

    if grant:
        restricted_license_permission.grant()

    # Raises PermissionDeniedError if not granted permission.
    record_test.data["metadata"]["rights"] = [{"id": "cc-by-nd-4.0"}]
    with outcome:
        result = record_test.update_draft()
        assert result["metadata"]["rights"][0]["id"] == "cc-by-nd-4.0"
