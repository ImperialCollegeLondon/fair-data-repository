"""Tests for the Description file transfer type."""

from io import BytesIO

import pytest
from ic_data_repo.permissions import described_file_action
from invenio_access.permissions import ActionUsers
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records_resources.services.errors import PermissionDeniedError
from marshmallow.exceptions import ValidationError


def test_description_transfer(
    vocabularies, icl_community, user_depositor, metadata, db
):
    """Test creating a DescriptionTransfer file."""
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record["status"] == "draft_with_review"

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
    r = current_rdm_records_service.draft_files.init_files(
        user_depositor.identity,
        record.id,
        data=file_metadata,
    )
    assert len(list(r.entries)) == 1

    # Upload the file.
    r = current_rdm_records_service.draft_files.set_file_content(
        user_depositor.identity,
        record.id,
        file_metadata[0]["key"],
        BytesIO(b"Test file content"),
    )
    assert r.errors is None

    # Commit the file.
    r = current_rdm_records_service.draft_files.commit_file(
        user_depositor.identity,
        record.id,
        file_metadata[0]["key"],
    )
    assert r.errors is None
    assert r["status"] == "completed"
    assert r["key"] == file_metadata[0]["key"]
    assert r["transfer"] == file_metadata[0]["transfer"]


def test_description_transfer_mixed_files(
    vocabularies, icl_community, user_depositor, metadata, db
):
    """Test creating mixed DescriptionTransfer and Local files."""
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record["status"] == "draft_with_review"

    # Grant permission to the user.
    db.session.add(
        ActionUsers.allow(described_file_action, user_id=user_depositor.user.id)
    )
    db.session.flush()

    # Metadata for a description transfer file and a local transfer file.
    file_metadata = [
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

    # Adding the description transfer file.
    r = current_rdm_records_service.draft_files.init_files(
        user_depositor.identity,
        record.id,
        data=file_metadata,
    )
    assert len(list(r.entries)) == 2

    for meta in file_metadata:
        # Upload the file.
        r = current_rdm_records_service.draft_files.set_file_content(
            user_depositor.identity,
            record.id,
            meta["key"],
            BytesIO(b"Test file content"),
        )
        assert r.errors is None

        # Commit the file.
        r = current_rdm_records_service.draft_files.commit_file(
            user_depositor.identity,
            record.id,
            meta["key"],
        )
        assert r.errors is None
        assert r["status"] == "completed"
        assert r["key"] == meta["key"]
        assert r["transfer"] == meta["transfer"]


def test_description_transfer_unauthorised_create(
    vocabularies, icl_community, user_depositor, metadata
):
    """Test creating a DescriptionTransfer file without permission."""
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record["status"] == "draft_with_review"

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
    with pytest.raises(PermissionDeniedError):
        current_rdm_records_service.draft_files.init_files(
            user_depositor.identity,
            record.id,
            data=file_metadata,
        )


def test_description_transfer_unauthorised_upload(
    vocabularies, icl_community, user_depositor, metadata, db
):
    """Test uploading a DescriptionTransfer file without permission."""
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record["status"] == "draft_with_review"

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
    r = current_rdm_records_service.draft_files.init_files(
        user_depositor.identity,
        record.id,
        data=file_metadata,
    )
    assert len(list(r.entries)) == 1

    # Revoke the permission from the user.
    db.session.delete(grant)
    db.session.flush()

    # Try to upload the file.
    with pytest.raises(PermissionDeniedError):
        current_rdm_records_service.draft_files.set_file_content(
            user_depositor.identity,
            record.id,
            file_metadata[0]["key"],
            BytesIO(b"Test file content"),
        )


def test_description_transfer_unauthorised_commit(
    vocabularies, icl_community, user_depositor, metadata, db
):
    """Test committing a DescriptionTransfer file without permission."""
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record["status"] == "draft_with_review"

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
    r = current_rdm_records_service.draft_files.init_files(
        user_depositor.identity,
        record.id,
        data=file_metadata,
    )
    assert len(list(r.entries)) == 1

    # Upload the file.
    r = current_rdm_records_service.draft_files.set_file_content(
        user_depositor.identity,
        record.id,
        file_metadata[0]["key"],
        BytesIO(b"Test file content"),
    )
    assert r.errors is None

    # Revoke the permission from the user.
    db.session.delete(grant)
    db.session.flush()

    # Try to commit the file.
    with pytest.raises(PermissionDeniedError):
        current_rdm_records_service.draft_files.commit_file(
            user_depositor.identity,
            record.id,
            file_metadata[0]["key"],
        )


def test_description_transfer_oversized_description(
    vocabularies, icl_community, user_depositor, metadata, db
):
    """Test creating a DescriptionTransfer file with an oversized description."""
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record["status"] == "draft_with_review"

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

    # Adding the description transfer file with oversized description.
    with pytest.raises(ValidationError, match="Longer than maximum length 100"):
        current_rdm_records_service.draft_files.init_files(
            user_depositor.identity,
            record.id,
            data=file_metadata,
        )
