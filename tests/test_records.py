"""Tests for records."""

from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service


def test_new_record_version(location, vocabularies, user_depositor, metadata):
    """Test creating a new version of a record."""
    record_v1_data = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {"imperial:dart_id": "123456789"},
    }
    record_v1 = current_rdm_records_service.create(
        user_depositor.identity, data=record_v1_data
    )
    assert record_v1["status"] == "draft"
    record_v1_published = current_rdm_records_service.publish(
        system_identity, record_v1.id
    )
    assert record_v1_published["status"] == "published"

    # Create version 2 of the record.
    record_v2 = current_rdm_records_service.new_version(
        user_depositor.identity, record_v1_published.id
    )
    assert record_v2["status"] == "new_version_draft"
    record_v2_published = current_rdm_records_service.publish(
        system_identity, record_v2.id
    )
    assert record_v2_published["status"] == "published"
