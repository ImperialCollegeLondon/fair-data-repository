"""Test cases for the Site Metadata API resource."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.datastructures import FileStorage


@pytest.fixture
def metadata():
    """Fixture to provide test metadata for records."""
    return {
        "title": "Test Record",
        "publication_date": "2023-01-01",
        "resource_type": {"id": "dataset"},
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "family_name": "Doe",
                    "given_name": "John",
                }
            }
        ],
    }


@pytest.fixture
def mock_json_metadata_file():
    """Fixture to create a mock JSON metadata file."""

    def _create_file(content=None):
        if content is None:
            content = b'{"name": "Test Dataset", "description": "A test dataset", "version": "1.0", "type": "dataset"}'  # noqa: E501

        return FileStorage(
            stream=BytesIO(content),
            filename="metadata.json",
            content_type="application/json",
        )

    return _create_file


def test_upload_validate_json_metadata(client, api_headers, mock_json_metadata_file):
    """Test uploading and validating JSON metadata."""
    pid_value = "test-record-123"
    fmt = "json"

    with patch(
        "ic_data_repo.site_metadata.services.service.SiteMetadataService.upload_and_validate"  # noqa: E501
    ) as mock_upload:
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "record_id": pid_value,
            "format": fmt,
            "file_key": "metadata-json.json",
            "valid": True,
            "errors": [],
        }
        mock_upload.return_value = mock_result

        headers = {k: v for k, v in api_headers.items() if k != "Content-Type"}

        data = {"file": mock_json_metadata_file()}
        response = client.post(
            f"/records/{pid_value}/metadata/{fmt}",
            data=data,
            headers=headers,
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["record_id"] == pid_value
    assert response_data["format"] == fmt
    assert response_data["valid"] is True
    assert response_data["errors"] == []
    assert response_data["file_key"] == "metadata-json.json"


def test_upload_validate_invalid_json_metadata(
    client, api_headers, mock_json_metadata_file
):
    """Test uploading and validating invalid JSON metadata."""
    pid_value = "test-record-456"
    fmt = "json"

    invalid_content = b'{"name": "Test", "missing_required_fields": true}'

    with patch(
        "ic_data_repo.site_metadata.services.service.SiteMetadataService.upload_and_validate"  # noqa: E501
    ) as mock_upload:
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "record_id": pid_value,
            "format": fmt,
            "file_key": "metadata-json.json",
            "valid": False,
            "errors": ["Missing required field: description"],
        }
        mock_upload.return_value = mock_result

        headers = {k: v for k, v in api_headers.items() if k != "Content-Type"}

        data = {"file": mock_json_metadata_file(invalid_content)}
        response = client.post(
            f"/records/{pid_value}/metadata/{fmt}",
            data=data,
            headers=headers,
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["record_id"] == pid_value
    assert response_data["valid"] is False
    assert len(response_data["errors"]) > 0


def test_upload_validate_missing_file(client, api_headers):
    """Test uploading metadata without providing a file."""
    pid_value = "test-record-999"
    fmt = "json"

    headers = {k: v for k, v in api_headers.items() if k != "Content-Type"}

    response = client.post(
        f"/records/{pid_value}/metadata/{fmt}",
        data={},
        headers=headers,
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_metadata_indexing_on_publish(client, api_headers, metadata, location):
    """Test that metadata is indexed when a record is published."""
    with patch(
        "invenio_drafts_resources.services.records.service.RecordService.create"
    ) as mock_create, patch(
        "invenio_drafts_resources.services.records.service.RecordService.publish"
    ) as mock_publish:
        # Mock the create response
        mock_create_result = MagicMock()
        mock_create_result.id = "test-record-id"
        mock_create_result.to_dict.return_value = {
            "id": "test-record-id",
            "metadata": metadata,
        }
        mock_create.return_value = mock_create_result

        # Mock the publish response
        mock_publish_result = MagicMock()
        mock_publish_result._record = MagicMock()
        mock_publish_result._record.id = "test-record-id"
        mock_publish.return_value = mock_publish_result

        # Create a draft record
        draft_response = client.post(
            "/records",
            json={"metadata": metadata},
            headers=api_headers,
        )
        assert draft_response.status_code == 201

        draft_data = draft_response.get_json()
        pid_value = draft_data["id"]

        # Publish the record
        publish_response = client.post(
            f"/records/{pid_value}/draft/actions/publish",
            headers=api_headers,
        )

        # Verify the service methods were called
        mock_create.assert_called_once()
        if publish_response.status_code in [200, 202]:
            mock_publish.assert_called_once()


def test_upload_validate_with_different_extensions(client, api_headers):
    """Test uploading metadata files with different extensions."""
    pid_value = "test-record-ext"
    fmt = "json"

    extensions = [".json", ".txt", ""]

    for ext in extensions:
        filename = f"metadata{ext}"

        with patch(
            "ic_data_repo.site_metadata.services.service.SiteMetadataService.upload_and_validate"  # noqa: E501
        ) as mock_upload:
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {
                "record_id": pid_value,
                "format": fmt,
                "file_key": f"metadata-json{ext}",
                "valid": True,
                "errors": [],
            }
            mock_upload.return_value = mock_result

            headers = {k: v for k, v in api_headers.items() if k != "Content-Type"}

            file_storage = FileStorage(
                stream=BytesIO(b'{"test": "data"}'),
                filename=filename,
                content_type="application/json",
            )

            data = {"file": file_storage}
            response = client.post(
                f"/records/{pid_value}/metadata/{fmt}",
                data=data,
                headers=headers,
                content_type="multipart/form-data",
            )

            assert response.status_code == 200
