"""Tests for the Description file transfer type."""

from ic_data_repo.permissions import described_file_action
from invenio_access.permissions import ActionUsers


def test_description_transfer(
    client,
    location,
    vocabularies,
    user_depositor,
    db,
    api_headers,
    api_file_upload_headers,
    metadata,
):
    """Test creating a DescriptionTransfer file."""
    record = client.post("/records", json={"metadata": metadata}, headers=api_headers)
    assert record.status_code == 201
    record_id = record.json["id"]

    # Grant permission to the user.
    db.session.add(
        ActionUsers.allow(described_file_action, user_id=user_depositor.user.id)
    )
    db.session.flush()

    # Metadata for the description transfer file.
    file_metadata = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
    ]

    # Adding the description transfer file.
    r = client.post(
        f"/records/{record_id}/draft/files",
        json=file_metadata,
        headers=api_headers,
    )
    assert r.status_code == 201
    assert len(r.json["entries"]) == 1
    assert r.json["entries"][0]["key"] == "dataset.zip"
    assert r.json["entries"][0]["transfer"]["type"] == "D"
    assert len(r.json["entries"][0]["transfer"]["description"]) == 100

    # Upload the file.
    r = client.put(
        f"/records/{record_id}/draft/files/dataset.zip/content",
        data=b"Test file content",
        headers=api_file_upload_headers,
    )
    assert r.status_code == 200

    # Commit the file.
    r = client.post(
        f"/records/{record_id}/draft/files/dataset.zip/commit",
        headers=api_headers,
    )
    assert r.status_code == 200


def test_description_transfer_mixed_files(
    client,
    location,
    vocabularies,
    user_depositor,
    db,
    api_headers,
    metadata,
):
    """Test creating mixed DescriptionTransfer and Local files."""
    record = client.post("/records", json={"metadata": metadata}, headers=api_headers)
    assert record.status_code == 201
    record_id = record.json["id"]

    # Grant permission to the user.
    db.session.add(
        ActionUsers.allow(described_file_action, user_id=user_depositor.user.id)
    )
    db.session.flush()

    # Metadata for a description transfer file and a local transfer file.
    file_metadata = []
    file_metadata.append(
        {
            "key": "described_dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        }
    )
    file_metadata.append(
        {
            "key": "local_dataset.zip",
            "transfer": {"type": "L"},
        }
    )

    # Adding the description transfer file.
    r = client.post(
        f"/records/{record_id}/draft/files",
        json=file_metadata,
        headers=api_headers,
    )
    assert r.status_code == 201
    assert len(r.json["entries"]) == 2
    assert r.json["entries"][0]["key"] == "described_dataset.zip"
    assert r.json["entries"][0]["transfer"]["type"] == "D"
    assert r.json["entries"][1]["key"] == "local_dataset.zip"
    assert r.json["entries"][1]["transfer"]["type"] == "L"


def test_description_transfer_unauthorised_create(
    client,
    location,
    vocabularies,
    user_depositor,
    db,
    api_headers,
    metadata,
):
    """Test creating a DescriptionTransfer file without permission."""
    record = client.post("/records", json={"metadata": metadata}, headers=api_headers)
    assert record.status_code == 201
    record_id = record.json["id"]

    # Metadata for the description transfer file.
    file_metadata = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
    ]

    # Adding the description transfer file.
    r = client.post(
        f"/records/{record_id}/draft/files",
        json=file_metadata,
        headers=api_headers,
    )
    assert r.status_code == 403


def test_description_transfer_unauthorised_upload(
    client,
    location,
    vocabularies,
    user_depositor,
    db,
    api_headers,
    api_file_upload_headers,
    metadata,
):
    """Test uploading a DescriptionTransfer file without permission."""
    record = client.post("/records", json={"metadata": metadata}, headers=api_headers)
    assert record.status_code == 201
    record_id = record.json["id"]

    grant = ActionUsers.allow(described_file_action, user_id=user_depositor.user.id)

    # Grant permission to the user.
    db.session.add(grant)
    db.session.flush()

    # Metadata for the description transfer file.
    file_metadata = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
    ]

    # Adding the description transfer file.
    r = client.post(
        f"/records/{record_id}/draft/files",
        json=file_metadata,
        headers=api_headers,
    )
    assert r.status_code == 201

    # Revoke the permission from the user.
    db.session.delete(grant)
    db.session.flush()

    # Try to upload the file.
    r = client.put(
        f"/records/{record_id}/draft/files/dataset.zip/content",
        data=b"Test file content",
        headers=api_file_upload_headers,
    )
    assert r.status_code == 403


def test_description_transfer_unauthorised_commit(
    client,
    location,
    vocabularies,
    user_depositor,
    db,
    api_headers,
    api_file_upload_headers,
    metadata,
):
    """Test committing a DescriptionTransfer file without permission."""
    record = client.post("/records", json={"metadata": metadata}, headers=api_headers)
    assert record.status_code == 201
    record_id = record.json["id"]

    grant = ActionUsers.allow(described_file_action, user_id=user_depositor.user.id)

    # Grant permission to the user.
    db.session.add(grant)
    db.session.flush()

    # Metadata for the description transfer file.
    file_metadata = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
    ]

    # Adding the description transfer file.
    r = client.post(
        f"/records/{record_id}/draft/files",
        json=file_metadata,
        headers=api_headers,
    )
    assert r.status_code == 201

    # Upload the file.
    r = client.put(
        f"/records/{record_id}/draft/files/dataset.zip/content",
        data=b"Test file content",
        headers=api_file_upload_headers,
    )
    assert r.status_code == 200

    # Revoke the permission from the user.
    db.session.delete(grant)
    db.session.flush()

    # Try to commit the file.
    r = client.post(
        f"/records/{record_id}/draft/files/dataset.zip/commit",
        headers=api_headers,
    )
    assert r.status_code == 403


def test_description_transfer_oversized_description(
    client,
    location,
    vocabularies,
    user_depositor,
    db,
    api_headers,
    metadata,
):
    """Test creating a DescriptionTransfer file with an oversized description."""
    record = client.post("/records", json={"metadata": metadata}, headers=api_headers)
    assert record.status_code == 201
    record_id = record.json["id"]

    # Grant permission to the user.
    db.session.add(
        ActionUsers.allow(described_file_action, user_id=user_depositor.user.id)
    )
    db.session.flush()

    # Metadata for the description transfer file.
    file_metadata = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 101,
            },
        },
    ]

    # Adding the description transfer file.
    r = client.post(
        f"/records/{record_id}/draft/files",
        json=file_metadata,
        headers=api_headers,
    )
    assert r.status_code == 400
