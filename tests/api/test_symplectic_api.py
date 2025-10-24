"""Test cases for the Symplectic API resource."""


def test_related_publications_endpoint(user_client):
    """Test that the related publications endpoint calls the service."""
    # test_client, mock_service = client

    # DOI search
    search_query = "10.1021/jp506459v"
    search_type = "doi"
    response = user_client.get(
        f"/symplectic/related-publications?search_query={search_query}&search_type={search_type}"  # noqa: E501
    )

    assert response.status_code == 200

    response_data = response.get_json()
    assert "results" in response_data
    assert "count" in response_data
    assert response_data["count"] == 2

    # # Title keyword search
    # mock_service.fetch_related_publications.reset_mock()
    # title_query = "catalysis"
    # response2 = test_client.get(
    #     f"/symplectic/related-publications?search_query={title_query}&search_type=title_keyword"  # noqa: E501
    # )
    # assert response2.status_code == 200
    # mock_service.fetch_related_publications.assert_called_once()
    # args2, _ = mock_service.fetch_related_publications.call_args
    # assert len(args2) == 3
    # assert args2[1] == title_query
    # assert args2[2] == "title_keyword"
