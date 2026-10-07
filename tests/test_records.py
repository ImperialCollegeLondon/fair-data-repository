"""Tests for records."""

from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_requests.proxies import current_requests_service


def test_new_record_version(vocabularies, icl_community, user_depositor, metadata):
    """Test creating a new version of a record."""
    record_v1_data = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {"imperial:dart_id": "123456789"},
    }
    record_v1 = current_rdm_records_service.create(
        user_depositor.identity,
        data=record_v1_data,
    )
    assert record_v1["status"] == "draft_with_review"

    # Submit the record to the Imperial community for review.
    review = current_rdm_records_service.review.submit(
        user_depositor.identity,
        record_v1.id,
        data={},
        require_review=True,
    )
    assert review["status"] == "submitted"

    # System accepts the community submission.
    current_requests_service.execute_action(
        system_identity,
        review.id,
        "accept",
        data={},
    )

    # Create version 2 of the record.
    record_v2 = current_rdm_records_service.new_version(
        user_depositor.identity, record_v1.id
    )
    assert record_v2["status"] == "new_version_draft"

    # Publish the new version of the record.
    record_v2_published = current_rdm_records_service.publish(
        user_depositor.identity, record_v2.id
    )
    assert record_v2_published["status"] == "published"
