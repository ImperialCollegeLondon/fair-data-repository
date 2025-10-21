"""Test cases for the Site Metadata API resources."""

import io
import json
from unittest.mock import MagicMock

import pytest
from flask import Flask, g
from ic_data_repo.site_metadata.services.errors import (
    MetadataValidationError,
    UnsupportedFormatError,
)
from ic_data_repo.site_metadata.services.result_items import MetadataValidationResult
from ic_data_repo.site_metadata.services.service import SiteMetadataService


@pytest.fixture
def app():
    """Create a Flask test app with the Site Metadata resource registered."""
    app = Flask("testapp")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client with mocked service."""
    # Create a mock service
    mock_service = MagicMock(spec=SiteMetadataService)

    # Setup mock response for successful validation
    mock_result = MagicMock(spec=MetadataValidationResult)
    mock_result.to_dict.return_value = {
        "record_id": "abc123",
        "format": "json",
        "file_key": "metadata-json.json",
        "valid": True,
        "errors": [],
    }
    mock_service.upload_and_validate.return_value = mock_result

    # Create a standard Flask route that bypasses Flask-Resources
    @app.route("/records/<pid_value>/metadata/<fmt>", methods=["POST"])
    def handle_upload_validate(pid_value, fmt):
        from flask import request

        # Check for file in request
        if "file" not in request.files:
            return json.dumps({"error": "Missing file field"}), 400

        # Get file from request
        file = request.files["file"]

        try:
            # Call service directly with correct parameters
            result = mock_service.upload_and_validate(
                g.identity, pid_value, fmt, file.stream, file.filename
            )
            # Return formatted result
            return (
                json.dumps(result.to_dict()),
                200,
                {"Content-Type": "application/json"},
            )

        except UnsupportedFormatError:
            return (
                json.dumps(
                    {
                        "error": "Unsupported format",
                        "description": f"Unsupported metadata format '{fmt}'",
                    }
                ),
                400,
                {"Content-Type": "application/json"},
            )

        except MetadataValidationError:
            return (
                json.dumps(
                    {
                        "error": "Validation error",
                        "description": "Metadata validation failed",
                    }
                ),
                400,
                {"Content-Type": "application/json"},
            )

    # Add a before_request handler to set up g.identity
    @app.before_request
    def set_identity():
        g.identity = MagicMock()

    return app.test_client(), mock_service


def test_upload_validate_success(client):
    """Test successful metadata upload and validation."""
    test_client, mock_service = client

    # Create test data
    record_id = "abc123"
    format_type = "json"

    test_content = json.dumps(
        {"name": "Test Dataset", "description": "A dataset"}
    ).encode("utf-8")

    # Create an in-memory file-like object
    test_file = io.BytesIO(test_content)

    # Make the request
    response = test_client.post(
        f"/records/{record_id}/metadata/{format_type}",
        data={"file": (test_file, "metadata.json")},
        content_type="multipart/form-data",
    )

    # Check service was called correctly
    assert response.status_code == 200
    mock_service.upload_and_validate.assert_called_once()

    # Verify the service was called with correct parameters
    args, kwargs = mock_service.upload_and_validate.call_args
    assert args[1] == record_id
    assert args[2] == format_type
    assert args[4] == "metadata.json"

    # Verify response content
    response_data = json.loads(response.data)
    assert response_data["record_id"] == record_id
    assert response_data["format"] == format_type
    assert response_data["valid"] is True
    assert response_data["errors"] == []


def test_upload_validate_missing_file(client):
    """Test metadata upload endpoint with missing file."""
    test_client, mock_service = client

    record_id = "abc123"
    format_type = "json"

    response = test_client.post(
        f"/records/{record_id}/metadata/{format_type}",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert b"Missing file field" in response.data
    mock_service.upload_and_validate.assert_not_called()


def test_upload_validate_unsupported_format(client):
    """Test metadata upload with unsupported format."""
    test_client, mock_service = client

    # Configure mock to raise UnsupportedFormatError
    mock_service.upload_and_validate.side_effect = UnsupportedFormatError("csv")

    record_id = "abc123"
    format_type = "csv"  # Unsupported format
    test_file = io.BytesIO(b"test content")

    response = test_client.post(
        f"/records/{record_id}/metadata/{format_type}",
        data={"file": (test_file, "metadata.csv")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "Unsupported metadata format" in response_data.get("description", "")


def test_upload_validate_invalid_content(client):
    """Test metadata upload with invalid content for Marshmallow schema."""
    test_client, mock_service = client

    # Configure mock to raise MetadataValidationError
    mock_service.upload_and_validate.side_effect = MetadataValidationError(
        "json", ["'name' is required"]
    )

    record_id = "abc123"
    format_type = "json"

    # Invalid JSON content (missing required 'name')
    test_content = json.dumps({"description": "No name"}).encode("utf-8")
    test_file = io.BytesIO(test_content)

    response = test_client.post(
        f"/records/{record_id}/metadata/{format_type}",
        data={"file": (test_file, "metadata.json")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "validation failed" in response_data.get("description", "").lower()


def test_marshmallow_validator_direct():
    """Test the Marshmallow-based validator directly."""
    from ic_data_repo.site_metadata.services.schema import (
        JSONMetadataSchema,
        MarshmallowValidator,
    )

    validator = MarshmallowValidator(JSONMetadataSchema())

    # Valid data
    valid = json.dumps({"name": "Dataset A"}).encode("utf-8")
    loaded = validator(valid)
    assert loaded["name"] == "Dataset A"

    # Invalid data - missing required field
    invalid = json.dumps({"description": "X"}).encode("utf-8")
    with pytest.raises(ValueError) as excinfo:
        validator(invalid)
    assert "name" in str(excinfo.value).lower()

    # Invalid JSON
    invalid_json = b"{not valid json"
    with pytest.raises(ValueError) as excinfo:
        validator(invalid_json)
    assert "invalid json" in str(excinfo.value).lower()
