"""Tests for the Symplectic API client."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from ic_data_repo.symplectic_interface import SymplecticClient
from lxml import etree

DUMMY_URL = "https://api.symplectic.example.com"
DUMMY_SUBSCRIPTION_KEY = "fake-api-key-1234"
DATACITE_PREFIX = "10.5281/"


@pytest.fixture
def client():
    """Create a Symplectic client instance with mocked environment variables."""
    return SymplecticClient(DUMMY_URL, DUMMY_SUBSCRIPTION_KEY)


@pytest.fixture
def datacite_prefix():
    """Provide a dummy datacite prefix for testing."""
    return DATACITE_PREFIX


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
            "related_identifiers": [
                {
                    "scheme": "doi",
                    "identifier": "10.5281/zenodo.783021",
                    "relation_type": {"id": "ispublishedin"},
                }
            ],
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
    assert client.api_url == DUMMY_URL
    assert client.api_key == DUMMY_SUBSCRIPTION_KEY
    assert client.headers == {
        "Content-Type": "text/xml",
        "Subscription-Key": DUMMY_SUBSCRIPTION_KEY,
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


def test_generate_record_xml(client, sample_metadata, datacite_prefix):
    """Test generating XML with minimal metadata."""
    xml = client.generate_record_xml(sample_metadata, datacite_prefix)
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

    # c-validated-doi from identifiers
    validated_doi_field = native.find(
        f".//{{{client.NAMESPACE_URI}}}field[@name='c-validated-doi']"
    )
    assert validated_doi_field is not None
    validated_doi_text = validated_doi_field.find(f"{{{client.NAMESPACE_URI}}}text")
    assert validated_doi_text is not None
    assert validated_doi_text.text.endswith(sample_metadata["id"])

    # c-related-doi from related_identifiers
    related_doi_field = native.find(
        f".//{{{client.NAMESPACE_URI}}}field[@name='c-related-doi']"
    )
    assert related_doi_field is not None
    related_doi_text = related_doi_field.find(f"{{{client.NAMESPACE_URI}}}text")
    assert related_doi_text is not None
    assert related_doi_text.text == "10.5281/zenodo.783021"


@patch("requests.put")
def test_create_record_success(mock_put, client, sample_metadata, datacite_prefix):
    """Test successful record creation by mocking the API response."""
    mock_put.return_value.content = b"""
    <api:response xmlns:api="http://www.symplectic.co.uk/publications/api">
        <api:object id="12345"/>
    </api:response>"""
    client.create_record(sample_metadata, datacite_prefix)

    expected_url = (
        f"{client.api_url}/publication/records/manual/{sample_metadata['id']}"
    )
    mock_put.assert_called_once()
    called_url = mock_put.call_args[0][0]
    called_headers = mock_put.call_args[1]["headers"]
    assert called_url == expected_url
    assert called_headers == client.headers


@patch("requests.put")
def test_create_record_failure(mock_put, client, sample_metadata):
    """Test record creation failure by mocking an unsuccessful API response."""
    mock_put().raise_for_status.side_effect = requests.exceptions.HTTPError(
        "400 Client Error", response=mock_put
    )
    mock_put.reset_mock()
    with pytest.raises(requests.exceptions.HTTPError):
        client.create_record(sample_metadata, datacite_prefix)
    expected_url = (
        f"{client.api_url}/publication/records/manual/{sample_metadata['id']}"
    )
    mock_put.assert_called_once()
    called_url = mock_put.call_args[0][0]
    called_headers = mock_put.call_args[1]["headers"]
    assert called_url == expected_url
    assert called_headers == client.headers


@patch("requests.put")
def test_create_record_minimal_metadata(
    mock_put, client, minimal_metadata, datacite_prefix
):
    """Test successful record creation with minimal metadata."""
    mock_put.return_value.content = b"""
    <api:response xmlns:api="http://www.symplectic.co.uk/publications/api">
        <api:object id="12345"/>
    </api:response>"""
    client.create_record(minimal_metadata, datacite_prefix)

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
    xml = client.generate_record_xml(minimal_metadata, datacite_prefix)
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

    abstract_field = native.find(
        f".//{{{client.NAMESPACE_URI}}}field[@name='abstract']"
    )
    assert abstract_field is None


@patch("requests.get")
def test_fetch_related_objects(mock_get, client):
    """Test fetching related objects with a DOI."""
    mock_response = MagicMock()
    mock_response.content = b"""
    <api:response xmlns:api="http://www.symplectic.co.uk/publications/api">
      <api:object id="67890" category="publication"/>
    </api:response>
    """
    mock_response.text = mock_response.content.decode("utf-8")
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    test_dois = ["10.5281/zenodo.123456"]
    related_id = client.fetch_related_objects(test_dois)

    assert related_id == "67890"
    mock_get.assert_called_once()
    assert "zenodo.123456" in mock_get.call_args[0][0]


@patch("requests.post")
def test_link_related_records(mock_post, client):
    """Test linking related records."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    from_id = "12345"
    to_id = "67890"
    client.link_related_records(from_id, to_id)

    mock_post.assert_called_once()
    called_url = mock_post.call_args[0][0]
    called_data = mock_post.call_args[1]["data"]
    assert called_url == f"{client.api_url}/relationships"
    assert f"publication({from_id})" in called_data
    assert f"publication({to_id})" in called_data
    assert "<type-id>1</type-id>" in called_data
