"""Test cases for the Symplectic API resource."""

from unittest.mock import MagicMock

import pytest
from flask import Flask, g
from ic_data_repo.symplectic.resources.config import SymplecticResourceConfig
from ic_data_repo.symplectic.resources.resource import SymplecticResource
from ic_data_repo.symplectic.services.result_items import SymplecticRelatedObjectsResult


@pytest.fixture
def app():
    """Create a Flask test app with the Symplectic resource registered."""
    app = Flask("testapp")
    app.config["TESTING"] = True

    # Configure test settings
    app.config["SYMPLECTIC_API_URL"] = "https://test-api.example.com"
    app.config["SYMPLECTIC_API_KEY"] = "test-api-key"

    return app


@pytest.fixture
def client(app):
    """Create a test client with mocked service."""
    # Create a mock service
    mock_service = MagicMock()

    # Setup mock response
    mock_result = MagicMock(spec=SymplecticRelatedObjectsResult)
    mock_result.to_dict.return_value = {
        "related_object_ids": ["123", "456"],
        "count": 2,
        "links": {"self": "/api/symplectic/related-objects"},
    }
    mock_service.fetch_related_objects.return_value = mock_result

    # Register the resource with the mocked service
    resource_config = SymplecticResourceConfig()
    resource = SymplecticResource(resource_config, mock_service)
    app.register_blueprint(resource.as_blueprint())

    # Add a before_request handler to set up g.identity
    @app.before_request
    def set_identity():
        g.identity = MagicMock()

    return app.test_client(), mock_service


def test_related_objects_endpoint(client):
    """Test that the related objects endpoint calls the service."""
    # Unpack client and mock service
    test_client, mock_service = client

    # Make a request to the endpoint
    doi = "10.1021/jp506459v"
    response = test_client.get(f"/symplectic/related-objects?doi={doi}")

    # Check response status
    assert response.status_code == 200

    # Check service was called with correct arguments
    mock_service.fetch_related_objects.assert_called_once()
    args, kwargs = mock_service.fetch_related_objects.call_args
    assert len(args) == 2
    assert args[1] == doi  # Second arg should be the DOI

    # Check response content
    response_data = response.get_json()
    assert "related_object_ids" in response_data
    assert "count" in response_data
    assert response_data["count"] == 2
