"""Tests for the Description file transfer type."""

import pytest
from ic_data_repo.permissions import described_file_action
from invenio_records_resources.services.errors import PermissionDeniedError
from marshmallow.exceptions import ValidationError


@pytest.fixture
def record(record_tester):
    """Fixture for creating a record with files enabled."""
    record_test = record_tester()
    record_test.data["files"] = {"enabled": True}
    return record_test.create()


def test_description_transfer(permission_manager, record, files_tester):
    """Test creating a DescriptionTransfer file."""
    permission_manager(described_file_action).grant()

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
    files_test = files_tester(record.id, files_data)

    # Test initialising the draft files.
    result = files_test.init()
    assert len(list(result.entries)) == len(files_data)

    # Test uploading the draft files.
    result = files_test.upload()
    assert result[0].errors is None

    # Test committing the draft files.
    result = files_test.commit()
    assert result[0].errors is None
    assert result[0]["key"] == files_data[0]["key"]
    assert result[0]["transfer"] == files_data[0]["transfer"]


def test_description_transfer_mixed_files(permission_manager, record, files_tester):
    """Test creating mixed DescriptionTransfer and Local files."""
    permission_manager(described_file_action).grant()

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
    files_test = files_tester(record.id, files_data)

    # Test initialising the draft files.
    result = files_test.init()
    assert len(list(result.entries)) == len(files_data)

    # Test uploading the draft files.
    result = files_test.upload()
    assert all(r.errors is None for r in result)

    # Test committing the draft files.
    result = files_test.commit()
    assert all(r.errors is None for r in result)
    assert result[0]["key"] == files_data[0]["key"]
    assert result[0]["transfer"] == files_data[0]["transfer"]
    assert result[1]["key"] == files_data[1]["key"]
    assert result[1]["transfer"] == files_data[1]["transfer"]


def test_description_transfer_unauthorised_create(record, files_tester):
    """Test creating a DescriptionTransfer file without permission."""
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
    files_test = files_tester(record.id, files_data)

    # Adding the description transfer file.
    with pytest.raises(PermissionDeniedError):
        files_test.init()


def test_description_transfer_unauthorised_upload(
    permission_manager, record, files_tester
):
    """Test uploading a DescriptionTransfer file without permission."""
    described_file_permission = permission_manager(described_file_action).grant()

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
    files_test = files_tester(record.id, files_data)

    # Adding the description transfer file.
    files_test.init()

    described_file_permission.revoke()

    # Try to upload the file.
    with pytest.raises(PermissionDeniedError):
        files_test.upload()


def test_description_transfer_unauthorised_commit(
    permission_manager, record, files_tester
):
    """Test committing a DescriptionTransfer file without permission."""
    described_file_permission = permission_manager(described_file_action).grant()

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
    files_test = files_tester(record.id, files_data)

    # Adding the description transfer file.
    files_test.init()

    # Upload the file.
    files_test.upload()

    described_file_permission.revoke()

    # Try to commit the file.
    with pytest.raises(PermissionDeniedError):
        files_test.commit()


def test_description_transfer_oversized_description(
    permission_manager, record, files_tester
):
    """Test creating a DescriptionTransfer file with an oversized description."""
    permission_manager(described_file_action).grant()

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
    files_test = files_tester(record.id, files_data)

    # Adding the description transfer file with oversized description.
    with pytest.raises(ValidationError, match="Longer than maximum length 100"):
        files_test.init()
