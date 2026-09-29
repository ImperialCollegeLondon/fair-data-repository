"""Test cases for the Symplectic API resource."""

from unittest.mock import MagicMock, patch  # added

import pytest


@pytest.fixture
def mock_symplectic_response():
    """Fixture to mock Symplectic API responses."""

    def _mock_response(xml_content=None, status_code=200):
        if xml_content is None:
            xml_content = b"""
            <api:response xmlns:api="http://www.symplectic.co.uk/publications/api">
                <api:object id="12345" category="publication">
                    <api:record>
                        <api:native>
                            <api:field name="title" type="text">
                                <api:text>Test Title</api:text>
                            </api:field>
                            <api:field name="doi" type="text">
                                <api:text>10.1234/test-doi</api:text>
                            </api:field>
                        </api:native>
                    </api:record>
                </api:object>
                <api:object id="67890" category="publication">
                    <api:record>
                        <api:native>
                            <api:field name="title" type="text">
                                <api:text>Another Test Title</api:text>
                            </api:field>
                            <api:field name="doi" type="text">
                                <api:text>10.5678/another-doi</api:text>
                            </api:field>
                        </api:native>
                    </api:record>
                </api:object>
            </api:response>
            """

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = xml_content
        mock_response.text = xml_content.decode("utf-8")
        mock_response.status_code = status_code
        return mock_response

    return _mock_response


def test_related_publications_endpoint(user_client, mock_symplectic_response):
    """Test that the related publications endpoint calls the service."""
    search_query = "test"
    search_type = "title-keywords"

    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_symplectic_response()

        response = user_client.get(
            f"/symplectic/related-publications?search_query={search_query}&search_type={search_type}"
        )

    assert response.status_code == 200
    response_data = response.get_json()
    assert "results" in response_data
    assert "count" in response_data
    assert response_data["count"] == 2
    assert len(response_data["results"]) == 2

    # Check first publication
    first_pub = response_data["results"][0]
    assert first_pub["id"] == "12345"
    assert first_pub["title"] == "Test Title"
    assert first_pub["doi"] == "10.1234/test-doi"
    assert first_pub["doi"].startswith("10.")

    # Check second publication
    second_pub = response_data["results"][1]
    assert second_pub["id"] == "67890"
    assert second_pub["title"] == "Another Test Title"
    assert second_pub["doi"] == "10.5678/another-doi"
    assert second_pub["doi"].startswith("10.")

    # Verify all results have DOIs
    for pub in response_data["results"]:
        assert "doi" in pub
        assert pub["doi"] is not None
        assert isinstance(pub["doi"], str)
        assert len(pub["doi"]) > 0


def test_related_publications_invalid_search_type(user_client):
    """Test that invalid search type returns 400 error."""
    search_query = "test"
    invalid_search_type = "invalid-type"
    response = user_client.get(
        f"/symplectic/related-publications?search_query={search_query}&search_type={invalid_search_type}"
    )

    assert response.status_code == 400
    response_data = response.get_json()
    assert "message" in response_data


def test_returning_error_from_symplectic(user_client, mock_symplectic_response):
    """Test that an error from Symplectic API is handled properly."""
    search_query = "test"
    search_type = "title-keywords"

    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_symplectic_response(
            xml_content=b"<api:error>Invalid request</api:error>", status_code=500
        )

        response = user_client.get(
            f"/symplectic/related-publications?search_query={search_query}&search_type={search_type}"
        )

    assert response.status_code == 500
    response_data = response.get_json()
    assert "message" in response_data
