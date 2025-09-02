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
        "results": [
            {"id": "123", "title": "Paper Title 1", "doi": "10.1021/jp506459v"},
            {"id": "456", "title": "Paper Title 2", "doi": "10.1234/example"},
        ],
        "count": 2,
        "links": {"self": "/api/symplectic/related-objects"},
    }
    mock_service.fetch_related_publications.return_value = mock_result

    # Register the resource with the mocked service
    resource_config = SymplecticResourceConfig()
    resource = SymplecticResource(resource_config, mock_service)
    app.register_blueprint(resource.as_blueprint())

    # Add a before_request handler to set up g.identity
    @app.before_request
    def set_identity():
        g.identity = MagicMock()

    return app.test_client(), mock_service


def test_related_publications_endpoint(client):
    """Test that the related publications endpoint calls the service."""
    test_client, mock_service = client

    # DOI search
    search_query = "10.1021/jp506459v"
    search_type = "doi"
    response = test_client.get(
        f"/symplectic/related-publications?search_query={search_query}&search_type={search_type}"  # noqa: E501
    )

    assert response.status_code == 200

    # Service should have been called with (identity, search_query, search_type)
    mock_service.fetch_related_publications.assert_called_once()
    args, kwargs = mock_service.fetch_related_publications.call_args
    assert len(args) == 3
    # args[0] is g.identity mock
    assert args[1] == search_query
    assert args[2] == search_type

    response_data = response.get_json()
    assert "results" in response_data
    assert "count" in response_data
    assert response_data["count"] == 2

    # Title keyword search
    mock_service.fetch_related_publications.reset_mock()
    title_query = "catalysis"
    response2 = test_client.get(
        f"/symplectic/related-publications?search_query={title_query}&search_type=title_keyword"  # noqa: E501
    )
    assert response2.status_code == 200
    mock_service.fetch_related_publications.assert_called_once()
    args2, _ = mock_service.fetch_related_publications.call_args
    assert len(args2) == 3
    assert args2[1] == title_query
    assert args2[2] == "title_keyword"
