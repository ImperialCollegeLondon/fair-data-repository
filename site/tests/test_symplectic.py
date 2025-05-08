"""Tests for the Symplectic API client."""

import os
import uuid
from unittest.mock import ANY, Mock, patch

import pytest
from ic_data_repo.symplectic_interface import SymplecticClient
from lxml import etree


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for the Symplectic client."""
    with patch.dict(
        os.environ,
        {
            "SYMPLECTIC_API_URL": "https://api.symplectic.example.com",
            "API_SUBSCRIPTION_KEY": "fake-api-key-1234",
        },
    ):
        yield


@pytest.fixture
def client(mock_env_vars):
    """Create a Symplectic client instance with mocked environment variables."""
    return SymplecticClient()


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing record creation."""
    return {
        "title": "Test Dataset Title",
        "abstract": "This is a sample abstract for testing purposes.",
        "authors": [
            {
                "first_names": "Alice",
                "last_name": "Researcher",
                "orcid": "0000-0001-2345-6789",
            },
            {"first_names": "Bob", "last_name": "Scientist"},
        ],
        "doi": "10.12345/test.67890",
        "publication_date": "2023-04-15",
        "licence": "CC-BY-4.0",
        "version": "1.0",
    }


def test_client_initialization(client):
    """Test that the client initializes with values from env."""
    assert client.api_url == "https://api.symplectic.example.com"
    assert client.api_key == "fake-api-key-1234"
    assert client.headers == {
        "Content-Type": "text/xml",
        "Subscription-Key": "fake-api-key-1234",
    }


def test_add_doi_subtree(client):
    """Test adding a DOI subtree to an XML element."""
    parent = etree.Element("test-parent")

    client.add_doi_subtree(parent, "c-validated-doi", "DOI", "10.12345/test.67890")

    field = parent.find(f"{{{client.NAMESPACE_URI}}}field")
    assert field is not None
    assert field.get("name") == "c-validated-doi"
    assert field.get("type") == "text"

    text = field.find(f"{{{client.NAMESPACE_URI}}}text")
    assert text is not None
    assert text.text == "10.12345/test.67890"

    links = field.find(f"{{{client.NAMESPACE_URI}}}links")
    assert links is not None

    link_elements = links.findall(f"{{{client.NAMESPACE_URI}}}link")
    assert len(link_elements) == 2

    doi_link = link_elements[0]
    assert doi_link.get("type") == "doi"
    assert doi_link.get("href") == "https://doi.org/10.12345/test.67890"

    altmetric_link = link_elements[1]
    assert altmetric_link.get("type") == "altmetric"
    assert (
        altmetric_link.get("href")
        == "https://www.altmetric.com/details.php?doi=10.12345/test.67890"
    )


def test_generate_record_xml(client, sample_metadata):
    """Test generating XML with full metadata."""
    xml = client.generate_record_xml(sample_metadata)
    native = xml.find(f"{{{client.NAMESPACE_URI}}}native")

    abstract_field = native.find(
        f".//{{{client.NAMESPACE_URI}}}field[@name='abstract']"
    )
    assert abstract_field is not None
    assert (
        abstract_field.find(f"{{{client.NAMESPACE_URI}}}text").text
        == "This is a sample abstract for testing purposes."
    )

    authors_field = native.find(f".//{{{client.NAMESPACE_URI}}}field[@name='authors']")
    assert authors_field is not None
    people = authors_field.find(f"{{{client.NAMESPACE_URI}}}people")
    persons = people.findall(f"{{{client.NAMESPACE_URI}}}person")
    assert len(persons) == 2

    assert persons[0].find(f"{{{client.NAMESPACE_URI}}}first-names").text == "Alice"
    assert persons[0].find(f"{{{client.NAMESPACE_URI}}}last-name").text == "Researcher"
    identifiers = persons[0].find(f"{{{client.NAMESPACE_URI}}}identifiers")
    assert identifiers is not None
    orcid = identifiers.find(f"{{{client.NAMESPACE_URI}}}identifier[@scheme='orcid']")
    assert orcid.text == "0000-0001-2345-6789"

    assert persons[1].find(f"{{{client.NAMESPACE_URI}}}first-names").text == "Bob"
    assert persons[1].find(f"{{{client.NAMESPACE_URI}}}last-name").text == "Scientist"
    assert persons[1].find(f"{{{client.NAMESPACE_URI}}}identifiers") is None

    licence_field = native.find(
        f".//{{{client.NAMESPACE_URI}}}field[@name='c-licence']"
    )
    assert licence_field is not None
    assert licence_field.find(f"{{{client.NAMESPACE_URI}}}text").text == "CC-BY-4.0"

    version_field = native.find(f".//{{{client.NAMESPACE_URI}}}field[@name='version']")
    assert version_field is not None
    assert version_field.find(f"{{{client.NAMESPACE_URI}}}text").text == "1.0"


def test_create_record_success(client, sample_metadata):
    """Test successful record creation by mocking the API response."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.headers = {"Location": "/publication/records/12345"}
    mock_response.text = "<api:response>Record created successfully</api:response>"
    mock_response.ok = True

    test_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")

    with patch("requests.put", return_value=mock_response) as mock_put, patch(
        "uuid.uuid4", return_value=test_uuid
    ):

        result = client.create_record(sample_metadata)

        expected_url = (
            f"{client.api_url}/publication/records/manual/{str(test_uuid).upper()}"
        )
        mock_put.assert_called_once_with(expected_url, data=ANY, headers=client.headers)

        assert result["status_code"] == 201
        assert result["headers"] == {"Location": "/publication/records/12345"}
        assert (
            result["content"]
            == "<api:response>Record created successfully</api:response>"
        )
        assert result["success"] is True
        assert result["proprietary_id"] == str(test_uuid)
        assert result["url"] == expected_url


def test_create_record_failure(client, sample_metadata):
    """Test record creation failure by mocking an error API response."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.headers = {"Content-Type": "application/xml"}
    mock_response.text = "<api:error>Invalid data</api:error>"
    mock_response.ok = False

    test_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")

    with patch("requests.put", return_value=mock_response) as mock_put, patch(
        "uuid.uuid4", return_value=test_uuid
    ):

        result = client.create_record(sample_metadata)

        mock_put.assert_called_once_with(
            f"{client.api_url}/publication/records/manual/{str(test_uuid).upper()}",
            data=ANY,
            headers=client.headers,
        )

        assert result["status_code"] == 400
        assert result["content"] == "<api:error>Invalid data</api:error>"
        assert result["success"] is False
