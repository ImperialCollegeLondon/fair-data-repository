"""Test cases for the Site Metadata API resource."""

from io import BytesIO

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service
from werkzeug.datastructures import FileStorage


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


@pytest.fixture
def create_test_record(client, api_headers, metadata, location, vocabularies):
    """Fixture to create a test record and return its PID."""
    response = client.post(
        "/records",
        json={"metadata": metadata, "files": {"enabled": True}},
        headers=api_headers,
    )
    assert response.status_code == 201
    draft_data = response.get_json()
    pid_value = draft_data["id"]

    return pid_value


def test_upload_validate_json_metadata(
    client, api_headers, mock_json_metadata_file, create_test_record, location
):
    """Test uploading and validating JSON metadata."""
    pid_value = create_test_record
    fmt = "json"

    # Remove Content-Type header for multipart/form-data
    headers = {k: v for k, v in api_headers.items() if k != "Content-Type"}

    metadata = b'{"name": "Test Dataset", "description": "A test dataset", "version": "1.0", "type": "dataset"}'  # noqa: E501
    data = {"file": (BytesIO(metadata), "metadata.json", "multipart/form-data")}

    response = client.post(
        f"/records/{pid_value}/metadata/{fmt}",
        data=data,
        headers=headers,
    )

    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["record_id"] == pid_value
    assert response_data["format"] == fmt
    assert response_data["valid"] is True
    assert response_data["errors"] == []
    assert response_data["file_key"] == "metadata.json"

    result = current_rdm_records_service.draft_files.list_files(
        system_identity, pid_value
    )
    files = list(result.entries)
    assert len(files) == 1
    assert "metadata.json" == files[0]["key"]
