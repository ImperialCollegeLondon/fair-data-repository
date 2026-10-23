"""Tests for the Description file transfer type."""

import pytest
from ic_data_repo.permissions import described_file_action
from invenio_records_resources.services.errors import PermissionDeniedError
from marshmallow.exceptions import ValidationError


def test_description_transfer(permission_manager, record, draft_files):
    """Test creating a DescriptionTransfer file."""
    described_file_permission = permission_manager(described_file_action)

    record = record(data_override={"files": {"enabled": True}})
    record.create()

    # Grant permission to the user.
    described_file_permission.grant()

    # Data for the description transfer file.
    files_data = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
    ]
    files = draft_files(record.id, files_data)

    # Test initialising the draft files.
    result = files.init()
    assert len(list(result.entries)) == len(files_data)

    # Test uploading the draft files.
    result = files.upload()
    assert result[0].errors is None

    # Test committing the draft files.
    result = files.commit()
    assert result[0].errors is None
    assert result[0]["key"] == files_data[0]["key"]
    assert result[0]["transfer"] == files_data[0]["transfer"]


def test_description_transfer_mixed_files(permission_manager, record, draft_files):
    """Test creating mixed DescriptionTransfer and Local files."""
    described_file_permission = permission_manager(described_file_action)

    record = record(data_override={"files": {"enabled": True}})
    record.create()

    # Grant permission to the user.
    described_file_permission.grant()

    # Data for a description transfer file and a local transfer file.
    files_data = [
        {
            "key": "described_dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
        {
            "key": "local_dataset.zip",
            "transfer": {"type": "L"},
        },
    ]
    files = draft_files(record.id, files_data)

    # Test initialising the draft files.
    result = files.init()
    assert len(list(result.entries)) == len(files_data)

    # Test uploading the draft files.
    result = files.upload()
    assert all(r.errors is None for r in result)

    # Test committing the draft files.
    result = files.commit()
    assert all(r.errors is None for r in result)
    assert result[0]["key"] == files_data[0]["key"]
    assert result[0]["transfer"] == files_data[0]["transfer"]
    assert result[1]["key"] == files_data[1]["key"]
    assert result[1]["transfer"] == files_data[1]["transfer"]


def test_description_transfer_unauthorised_create(record, draft_files):
    """Test creating a DescriptionTransfer file without permission."""
    record = record(data_override={"files": {"enabled": True}})
    record.create()

    # Data for the description transfer file.
    files_data = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
    ]
    files = draft_files(record.id, files_data)

    # Adding the description transfer file.
    with pytest.raises(PermissionDeniedError):
        files.init()


def test_description_transfer_unauthorised_upload(
    permission_manager, record, draft_files
):
    """Test uploading a DescriptionTransfer file without permission."""
    described_file_permission = permission_manager(described_file_action)

    record = record(data_override={"files": {"enabled": True}})
    record.create()

    # Grant permission to the user.
    described_file_permission.grant()

    # Data for the description transfer file.
    files_data = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
    ]
    files = draft_files(record.id, files_data)

    # Adding the description transfer file.
    files.init()

    # Revoke the permission from the user.
    described_file_permission.revoke()

    # Try to upload the file.
    with pytest.raises(PermissionDeniedError):
        files.upload()


def test_description_transfer_unauthorised_commit(
    permission_manager, record, draft_files
):
    """Test committing a DescriptionTransfer file without permission."""
    described_file_permission = permission_manager(described_file_action)

    record = record(data_override={"files": {"enabled": True}})
    record.create()

    # Grant permission to the user.
    described_file_permission.grant()

    # Data for the description transfer file.
    files_data = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 100,
            },
        },
    ]
    files = draft_files(record.id, files_data)

    # Adding the description transfer file.
    files.init()

    # Upload the file.
    files.upload()

    # Revoke the permission from the user.
    described_file_permission.revoke()

    # Try to commit the file.
    with pytest.raises(PermissionDeniedError):
        files.commit()


def test_description_transfer_oversized_description(
    permission_manager, record, draft_files
):
    """Test creating a DescriptionTransfer file with an oversized description."""
    described_file_permission = permission_manager(described_file_action)

    record = record(data_override={"files": {"enabled": True}})
    record.create()

    # Grant permission to the user.
    described_file_permission.grant()

    # Data for the description transfer file.
    files_data = [
        {
            "key": "dataset.zip",
            "transfer": {
                "type": "D",
                "description": "a" * 101,
            },
        },
    ]
    files = draft_files(record.id, files_data)

    # Adding the description transfer file with oversized description.
    with pytest.raises(ValidationError, match="Longer than maximum length 100"):
        files.init()
