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
