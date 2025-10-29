"""Test cases for the Symplectic API resource."""

from unittest.mock import MagicMock, patch  # added


def test_related_publications_endpoint(user_client):
    """Test that the related publications endpoint calls the service."""
    # Title-keywords search
    search_query = "test"
    search_type = "title-keywords"
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
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
        mock_response.text = mock_response.content.decode("utf-8")
        mock_get.return_value = mock_response

        response = user_client.get(
            f"/symplectic/related-publications?search_query={search_query}&search_type={search_type}"  # noqa E501
        )

    assert response.status_code == 200

    response_data = response.get_json()
    assert "results" in response_data
    assert "count" in response_data
    assert response_data["count"] == 2


def test_related_publications_invalid_search_type(user_client):
    """Test that an invalid search type returns a 500 error."""
    resp = user_client.get(
        "/symplectic/related-publications?search_query=x&search_type=not-supported"
    )
    assert resp.status_code == 500
