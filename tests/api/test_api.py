"""Tests for the API."""

from datetime import date

import pytest
from ic_data_repo.permissions import deposit_link_only_action
from invenio_access.permissions import ActionUsers


@pytest.fixture
def metadata():
    """Simple record metadata."""
    return {
        "title": "Test Record",
        "description": "This is a test record.",
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "given_name": "Neo",
                    "family_name": "Anderson",
                },
                "role": "the one",
            },
        ],
    }


@pytest.fixture
def link_only_file():
    """File metadata for a link-only transfer."""
    return [
        {
            "key": "example.txt",
            "size": 1234,
            "checksum": "md5:9e107d9d372bb6826bd81d3542a419d6",
            "transfer": {
                "type": "X",  # Link-only transfer type
                "url": "http://example.com/file.txt",
            },
        },
    ]


@pytest.fixture
def access():
    """Simple access schema."""
    return {
        "record": "public",
        "files": "public",
    }


def test_metadata_schema(
    client, location, vocabularies, user_depositor, api_headers, metadata, access
):
    """Test that the metadata schema is enforced."""
    metadata["resource_type"] = "fake_resource_type"
    metadata["publisher"] = "Fake Publisher"
    metadata["publication_date"] = "1970-01-01"
    access["record"] = "restricted"
    access["files"] = "restricted"
    result = client.post(
        "/records",
        json={"metadata": metadata, "access": access},
        headers=api_headers,
    )
    assert result.status_code == 201

    # Test metadata policies are enforced.
    assert result.json["metadata"]["title"] == "Test Record"
    assert result.json["metadata"]["resource_type"]["id"] == "dataset"
    assert (
        result.json["metadata"]["creators"][0]["person_or_org"]["given_name"] == "Neo"
    )
    assert "role" not in result.json["metadata"]["creators"][0]
    assert result.json["metadata"]["publisher"] == "Imperial College London"
    assert result.json["metadata"]["publication_date"] == date.today().isoformat()

    # Test access policies are enforced.
    # 'record' should be reset to public, but 'files' should remain restricted.
    assert result.json["access"]["record"] == "public"
    assert result.json["access"]["files"] == "restricted"


def test_metadata_schema_rights(
    client, location, vocabularies, user_depositor, api_headers, metadata
):
    """Test that the rights schema is enforced."""
    # Test that no license is accepted.
    metadata["rights"] = []
    result = client.post(
        "/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert "rights" not in result.json["metadata"]

    # Test that a single license is accepted.
    metadata["rights"] = [{"id": "cc0-1.0"}]
    result = client.post(
        "/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert result.json["metadata"]["rights"][0]["id"] == "cc0-1.0"

    # Test that multiple rights entries are not accepted.
    metadata["rights"] = [{"id": "cc0-1.0"}, {"id": "cc-by-4.0"}]
    result = client.post(
        "/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert result.json["errors"][0]["messages"][0].startswith("No more than")


def test_metadata_schema_copyright(
    client, location, vocabularies, user_depositor, api_headers, metadata
):
    """Test that the copyright metadata field is blocked."""
    metadata["copyright"] = "some data"
    result = client.post(
        "/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    error = result.json["errors"][0]
    assert error["field"] == "metadata.copyright"
    assert error["messages"] == ["Unknown field."]
    assert "copyright" not in result.json["metadata"]


def test_new_record_version(
    user_client, location, vocabularies, user_depositor, api_headers, metadata
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

    community_json = {
        "slug": "icl",
        "metadata": {"title": "Imperial College London"},
        "access": {"visibility": "public"},
    }
    community = user_client.post(
        "/communities",
        json=community_json,
        headers=api_headers,
    )
    assert community.status_code == 201
    community_id = community.json["id"]

    community_submit_json = {
        "receiver": {"community": community_id},
        "type": "community-submission",
    }
    community_submit = user_client.put(
        f"/records/{record_v1_id}/draft/review",
        json=community_submit_json,
        headers=api_headers,
    )
    assert community_submit.status_code == 200
    community_submit_id = community_submit.json["id"]

    comunity_review = user_client.post(
        f"/records/{record_v1_id}/draft/actions/submit-review",
        headers=api_headers,
    )
    assert comunity_review.status_code == 202

    accept_submission = user_client.post(
        f"/requests/{community_submit_id}/actions/accept", headers=api_headers
    )
    assert accept_submission.status_code == 200
    assert accept_submission.json["status"] == "accepted"

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


def test_link_only_file_transfer(
    client,
    location,
    vocabularies,
    user_depositor,
    db,
    api_headers,
    metadata,
    link_only_file,
):
    """Test the metadata fields used in the link-only file transfer type."""
    record = client.post("/records", json={"metadata": metadata}, headers=api_headers)
    assert record.status_code == 201
    record_id = record.json["id"]

    # Grant permission to the user.
    db.session.add(
        ActionUsers.allow(deposit_link_only_action, user_id=user_depositor.id)
    )

    # Adding a link-only file.
    response = client.post(
        f"/records/{record_id}/draft/files",
        json=link_only_file,
        headers=api_headers,
    )
    assert response.status_code == 201

    # Test link-only file metadata.
    file_metadata = response.json["entries"][0]
    assert file_metadata["key"] == "example.txt"
    assert file_metadata["size"] == 1234
    assert file_metadata["checksum"] == "md5:9e107d9d372bb6826bd81d3542a419d6"
    assert file_metadata["transfer"]["type"] == "X"
    assert file_metadata["transfer"]["url"] == "http://example.com/file.txt"


def test_link_only_file_transfer_without_permission(
    client,
    location,
    vocabularies,
    user_depositor,
    db,
    api_headers,
    metadata,
    link_only_file,
):
    """Test that link-only file transfer cannot be used without permission."""
    record = client.post("/records", json={"metadata": metadata}, headers=api_headers)
    assert record.status_code == 201
    record_id = record.json["id"]

    # Try adding a link-only file without permission.
    response = client.post(
        f"/records/{record_id}/draft/files",
        json=link_only_file,
        headers=api_headers,
    )
    assert response.status_code == 403
