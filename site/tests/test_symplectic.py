"""Tests for the Symplectic API client."""

import os
from unittest.mock import Mock, patch

import pytest
import requests
from ic_data_repo.symplectic_interface import SymplecticClient
from lxml import etree


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for the Symplectic client."""
    with patch.dict(
        os.environ,
        {
            "SYMPLECTIC_API_URL": "https://api.symplectic.example.com",
            "SYMPLECTIC_API_SUBSCRIPTION_KEY": "fake-api-key-1234",
        },
    ):
        yield


@pytest.fixture
def client(mock_env_vars):
    """Create a Symplectic client instance with mocked environment variables."""
    return SymplecticClient()


@pytest.fixture
def sample_metadata():
    """Provide sample metadata for testing."""
    return {
        "id": "test-12345",
        "metadata": {
            "title": "A title",
            "creators": [
                {
                    "person_or_org": {
                        "first_name": "John",
                        "type": "personal",
                        "family_name": "John",
                    }
                }
            ],
            "publisher": "Imperial College London",
            "resource_type": {"id": "dataset"},
            "publication_date": "2025-05-19",
        },
    }


@pytest.fixture
def minimal_metadata():
    """Provide minimal metadata for testing."""
    return {
        "id": "test-12345",
        "metadata": {
            "title": "A title",
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "John",
                    }
                }
            ],
            "publisher": "Imperial College London",
            "resource_type": {"id": "dataset"},
            "publication_date": "2025-05-19",
        },
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

    client.add_doi_subtree(parent, "c-validated-doi", "10.12345/test.67890")

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
    """Test generating XML with minimal metadata."""
    xml = client.generate_record_xml(sample_metadata)
    native = xml.find(f"{{{client.NAMESPACE_URI}}}native")

    title_field = native.find(f".//{{{client.NAMESPACE_URI}}}field[@name='title']")
    assert title_field is not None
    assert title_field.find(f"{{{client.NAMESPACE_URI}}}text").text == "A title"

    authors_field = native.find(f".//{{{client.NAMESPACE_URI}}}field[@name='authors']")
    assert authors_field is not None
    people = authors_field.find(f"{{{client.NAMESPACE_URI}}}people")
    persons = people.findall(f"{{{client.NAMESPACE_URI}}}person")
    assert len(persons) == 1
    assert persons[0].find(f"{{{client.NAMESPACE_URI}}}last-name").text == "John"


def test_create_record_success(client, sample_metadata):
    """Test successful record creation by mocking the API response."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.headers = {"Location": "/publication/records/12345"}
    mock_response.text = "<api:response>Record created successfully</api:response>"
    mock_response.ok = True
    mock_response.raise_for_status = Mock(return_value=None)

    with patch("requests.put", return_value=mock_response) as mock_put:
        client.create_record(sample_metadata)

        expected_url = (
            f"{client.api_url}/publication/records/manual/{sample_metadata['id']}"
        )
        mock_put.assert_called_once()
        called_url = mock_put.call_args[0][0]
        called_headers = mock_put.call_args[1]["headers"]
        assert called_url == expected_url
        assert called_headers == client.headers


def test_create_record_failure(client, sample_metadata):
    """Test record creation failure by mocking an unsuccessful API response."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "<api:response>Error creating record</api:response>"
    mock_response.ok = False

    mock_response.raise_for_status = Mock(
        side_effect=requests.exceptions.HTTPError(
            "400 Client Error", response=mock_response
        )
    )
    with patch("requests.put", return_value=mock_response) as mock_put:
        with pytest.raises(requests.exceptions.HTTPError):
            client.create_record(sample_metadata)

        expected_url = (
            f"{client.api_url}/publication/records/manual/{sample_metadata['id']}"
        )
        mock_put.assert_called_once()
        called_url = mock_put.call_args[0][0]
        called_headers = mock_put.call_args[1]["headers"]
        assert called_url == expected_url
        assert called_headers == client.headers


def test_create_record_minimal_metadata(client, minimal_metadata):
    """Test successful record creation with minimal metadata."""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.headers = {"Location": "/publication/records/12345"}
    mock_response.text = "<api:response>Record created successfully</api:response>"
    mock_response.ok = True
    mock_response.raise_for_status = Mock(return_value=None)

    with patch("requests.put", return_value=mock_response) as mock_put:
        client.create_record(minimal_metadata)

        expected_url = (
            f"{client.api_url}/publication/records/manual/{minimal_metadata['id']}"
        )
        mock_put.assert_called_once()
        called_url = mock_put.call_args[0][0]
        called_headers = mock_put.call_args[1]["headers"]
        assert called_url == expected_url
        assert called_headers == client.headers


def test_generate_record_xml_with_minimal_metadata(client, minimal_metadata):
    """Test generating XML with truly minimal metadata."""
    xml = client.generate_record_xml(minimal_metadata)
    native = xml.find(f"{{{client.NAMESPACE_URI}}}native")

    title_field = native.find(f".//{{{client.NAMESPACE_URI}}}field[@name='title']")
    assert title_field is not None
    assert title_field.find(f"{{{client.NAMESPACE_URI}}}text").text == "A title"

    authors_field = native.find(f".//{{{client.NAMESPACE_URI}}}field[@name='authors']")
    assert authors_field is not None
    people = authors_field.find(f"{{{client.NAMESPACE_URI}}}people")
    persons = people.findall(f"{{{client.NAMESPACE_URI}}}person")
    assert len(persons) == 1
    person = persons[0]
    assert person.find(f"{{{client.NAMESPACE_URI}}}last-name").text == "John"

    first_names_element = person.find(f"{{{client.NAMESPACE_URI}}}first-names")
    if first_names_element is not None:
        assert first_names_element.text is None or first_names_element.text == ""

    pub_date_field = native.find(
        f".//{{{client.NAMESPACE_URI}}}field[@name='publication-date']"
    )
    assert pub_date_field is not None
    date_element = pub_date_field.find(f"{{{client.NAMESPACE_URI}}}date")
    assert date_element is not None
    assert date_element.find(f"{{{client.NAMESPACE_URI}}}day").text == "19"
    assert date_element.find(f"{{{client.NAMESPACE_URI}}}month").text == "5"
    assert date_element.find(f"{{{client.NAMESPACE_URI}}}year").text == "2025"

    doi_field = native.find(
        f".//{{{client.NAMESPACE_URI}}}field[@name='c-validated-doi']"
    )
    assert doi_field is not None
    assert (
        doi_field.find(f"{{{client.NAMESPACE_URI}}}text").text == minimal_metadata["id"]
    )

    abstract_field = native.find(
        f".//{{{client.NAMESPACE_URI}}}field[@name='abstract']"
    )
    assert abstract_field is None

    version_field = native.find(f".//{{{client.NAMESPACE_URI}}}field[@name='version']")
    assert version_field is None
