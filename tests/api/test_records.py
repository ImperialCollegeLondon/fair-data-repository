"""Tests for records."""

from invenio_access.permissions import system_identity
from invenio_requests.proxies import current_requests_service


def test_new_record_version(
    user_client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """Test creating a new version of a record."""
    record_v1_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {"imperial:dart_id": "123456789"},
    }
    record_v1 = user_client.post(
        "/records",
        json=record_v1_json,
        headers=api_headers,
    )
    assert record_v1.status_code == 201
    record_v1_id = record_v1.json["id"]

    # Submit the record to the Imperial community for review.
    comunity_review = user_client.post(
        f"/records/{record_v1_id}/draft/actions/submit-review",
        headers=api_headers,
    )
    assert comunity_review.status_code == 202
    review_id = comunity_review.json["id"]

    # Admin accepts the community submission.
    current_requests_service.execute_action(
        system_identity, review_id, "accept", data={}
    )
    db.session.commit()

    # Create version 2 of the record.
    record_v2 = user_client.post(
        f"/records/{record_v1_id}/versions",
        headers=api_headers,
    )
    assert record_v2.status_code == 201
    record_v2_id = record_v2.json["id"]

    record_v2_published = user_client.post(
        f"/records/{record_v2_id}/draft/actions/publish",
        headers=api_headers,
    )
    assert record_v2_published.status_code == 202
