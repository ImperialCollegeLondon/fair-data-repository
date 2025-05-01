"""Symplectic API interface."""

import os
import uuid
from datetime import datetime
from functools import partial
from typing import Any, Dict

import requests
from dateutil.parser import parse as parse_date
from lxml import etree

API_SUBSCRIPTION_KEY = os.environ["API_SUBSCRIPTION_KEY"]

BASE_URL = "https://rma-001-apim.azure-api.net/symplectic/"

NAMESPACE_URI = "http://www.symplectic.co.uk/publications/records/manual"

etree.register_namespace("api", NAMESPACE_URI)
api_qname = partial(etree.QName, NAMESPACE_URI)


def add_doi_subtree(
    parent_element: etree.Element, doi_type: str, display_name: str, doi: str
):
    """Add a DOI subtree to the given parent element."""
    doi_element = etree.SubElement(
        parent_element,
        api_qname("field"),
        attrib={
            "name": doi_type,
            "type": "text",
            "display-name": doi_type,
        },
    )
    doi_text_element = etree.SubElement(
        doi_element,
        api_qname("text"),
    )
    doi_text_element.text = doi

    links_element = etree.SubElement(doi_element, api_qname("links"))
    doi_link_element = etree.SubElement(  # noqa: F841
        links_element,
        api_qname("link"),
        attrib={
            "type": "doi",
            "href": f"https://doi.org/{doi}",
        },
    )
    altmetric_link_element = etree.SubElement(  # noqa: F841
        links_element,
        api_qname("link"),
        attrib={
            "type": "altmetric",
            "href": f"https://www.altmetric.com/details.php?doi={doi}",
        },
    )


def generate_record_xml(
    title: str,
    abstract: str | None,
    authors: dict,
    licence: str | None,
    doi: str,
    version: str | None,
    publication_date: datetime,
):
    """Generate XML for a publication."""
    import_record_element = etree.Element(
        api_qname("import-record"),
        attrib={
            "type-name": "dataset",
            "type-id": "22",
        },
        nsmap={"api": "http://www.symplectic.co.uk/publications/api"},
    )
    native_element = etree.SubElement(
        import_record_element,
        api_qname("native"),
    )

    title_element = etree.SubElement(
        native_element,
        api_qname("field"),
        attrib={
            "name": "title",
            "type": "text",
            "display-name": "Title",
        },
    )
    title_text_element = etree.SubElement(
        title_element,
        api_qname("text"),
    )
    title_text_element.text = title

    if abstract:
        abstract_element = etree.SubElement(
            native_element,
            api_qname("field"),
            attrib={
                "name": "abstract",
                "type": "text",
                "display-name": "Abstract",
            },
        )
        abstract_text_element = etree.SubElement(
            abstract_element,
            api_qname("text"),  # , text=abstract
        )

    abstract_text_element.text = abstract

    authors_element = etree.SubElement(
        native_element,
        api_qname("field"),
        attrib={
            "name": "authors",
            "type": "person-list",
            "display-name": "Authors/Contributors",
        },
    )

    people_element = etree.SubElement(authors_element, api_qname("people"))
    for author in authors:
        person_element = etree.SubElement(people_element, api_qname("person"))
        last_name_element = etree.SubElement(person_element, api_qname("last-name"))
        last_name_element.text = author["last_name"]
        first_names_element = etree.SubElement(person_element, api_qname("first-names"))
        first_names_element.text = author["first_names"]
        if orcid := author.get("orcid"):
            identifiers_element = etree.SubElement(
                person_element, api_qname("identifiers")
            )
            orcid_element = etree.SubElement(
                identifiers_element,
                api_qname("identifier"),
                attrib=dict(scheme="orcid"),
            )
            orcid_element.text = orcid

    if licence:
        licence_element = etree.SubElement(
            native_element,
            api_qname("field"),
            attrib={
                "name": "c-licence",
                "type": "text",
                "display-name": "Licence",
            },
        )
        licence_text_element = etree.SubElement(licence_element, api_qname("text"))
        licence_text_element.text = licence

    add_doi_subtree(native_element, "c-validated-doi", "DOI", doi)

    if version:
        version_element = etree.SubElement(
            native_element,
            api_qname("field"),
            attrib={
                "name": "version",
                "type": "text",
                "display-name": "Version",
            },
        )
        version_text_element = etree.SubElement(version_element, api_qname("text"))
        version_text_element.text = version

    publication_date_element = etree.SubElement(
        native_element,
        api_qname("field"),
        attrib={
            "name": "publication-date",
            "type": "date",
            "display-name": "Publication Date",
        },
    )
    publication_date_date_element = etree.SubElement(
        publication_date_element, api_qname("date")
    )
    publication_day_element = etree.SubElement(
        publication_date_date_element, api_qname("day")
    )
    publication_day_element.text = str(publication_date.day)
    publication_month_element = etree.SubElement(
        publication_date_date_element, api_qname("month")
    )
    publication_month_element.text = str(publication_date.month)
    publication_year_element = etree.SubElement(
        publication_date_date_element, api_qname("year")
    )
    publication_year_element.text = str(publication_date.year)

    return import_record_element


class SymplecticClient:
    """A client for interacting with the Symplectic Elements API."""

    def __init__(self, base_url: str = BASE_URL, api_key: str = API_SUBSCRIPTION_KEY):
        """Initialize the Symplectic client.

        Args:
            base_url: The base URL for the Symplectic API.
            api_key: The API subscription key.
        """
        if not api_key:
            raise ValueError("API_SUBSCRIPTION_KEY must be set.")
        if not base_url:
            raise ValueError("SYMPLECTIC_BASE_URL must be set.")

        self.base_url = base_url.rstrip("/") + "/"
        self.headers = {
            "Content-Type": "text/xml",
            "Subscription-Key": api_key,
        }

    def extract_metadata(self, invenio_record: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts and transforms metadata from an Invenio record format."""
        metadata = invenio_record.get("metadata", {})
        pids = invenio_record.get("pids", {})

        doi = pids.get("doi", {}).get("identifier")
        if not doi:
            raise ValueError("Invenio record must have a DOI in pids.doi.identifier")

        authors = []
        for creator in metadata.get("creators", []):
            person_org = creator.get("person_or_org", {})
            if person_org.get("type") == "personal":
                author_data = {
                    "last_name": person_org.get("family_name"),
                    "first_names": person_org.get("given_name"),
                }
                for identifier in person_org.get("identifiers", []):
                    if identifier.get("scheme") == "orcid":
                        author_data["orcid"] = identifier.get("identifier")
                        break
                authors.append(author_data)

        licence_url = None
        rights = metadata.get("rights", [])
        if rights:
            licence_url = rights[0].get("link")

        pub_date_str = metadata.get("publication_date")
        if not pub_date_str:
            raise ValueError("Invenio record must have metadata.publication_date")
        try:
            publication_date = parse_date(pub_date_str)
        except ValueError as e:
            raise ValueError(f"Could not parse publication_date '{pub_date_str}': {e}")

        return {
            "title": metadata.get("title"),
            "abstract": metadata.get("description"),
            "authors": authors,
            "licence": licence_url,
            "doi": doi,
            "version": metadata.get("version"),
            "publication_date": publication_date,
        }

    def create_record(self, invenio_record: Dict[str, Any]) -> requests.Response:
        """Creates a new record in Symplectic Elements based on Invenio metadata.

        Args:
            invenio_record: A dictionary representing the Invenio record,
                            containing 'metadata' and 'pids' keys.

        Returns:
            The response object from the requests.put call.

        Raises:
            ValueError: If essential metadata (DOI, publication date) is missing
                        or cannot be parsed.
            requests.exceptions.RequestException: For issues during the API call.
        """
        if not isinstance(invenio_record, dict):
            raise TypeError("invenio_record must be a dictionary.")

        extracted_data = self.extract_metadata(invenio_record)

        record_xml_element = generate_record_xml(**extracted_data)
        record_xml_string = etree.tostring(record_xml_element, encoding="unicode")

        proprietary_id = uuid.uuid4()
        endpoint = f"publication/records/manual/{str(proprietary_id).upper()}"
        url = self.base_url + endpoint

        try:
            response = requests.put(
                url,
                data=record_xml_string.encode("utf-8"),
                headers=self.headers,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:

            print(f"Error creating Symplectic record: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise
