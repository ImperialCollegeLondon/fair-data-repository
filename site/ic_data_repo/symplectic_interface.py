"""Symplectic API client for creating records in Symplectic Elements."""

import os
from datetime import datetime
from functools import partial

import requests
from lxml import etree

NAMESPACE_URI = "http://www.symplectic.co.uk/publications/api"
etree.register_namespace("api", NAMESPACE_URI)
SYMPLECTIC_DATASET_TYPE_ID = "22"


class SymplecticClient:
    """Client for interacting with the Symplectic API."""

    NAMESPACE_URI = NAMESPACE_URI
    api_qname = partial(etree.QName, NAMESPACE_URI)

    def __init__(self, api_url=None, api_key=None):
        """Initialize the Symplectic client."""
        self.api_url = api_url or os.getenv("SYMPLECTIC_API_URL")
        self.api_key = api_key or os.getenv("SYMPLECTIC_API_SUBSCRIPTION_KEY")
        self.headers = {
            "Content-Type": "text/xml",
            "Subscription-Key": self.api_key,
        }

    def add_doi_subtree(self, parent_element, doi_type, doi):
        """Add a DOI subtree to the XML tree."""
        doi_element = etree.SubElement(
            parent_element,
            self.api_qname("field"),
            attrib={
                "name": doi_type,
                "type": "text",
                "display-name": doi_type,
            },
        )
        doi_text_element = etree.SubElement(
            doi_element,
            self.api_qname("text"),
        )
        doi_text_element.text = doi

        links_element = etree.SubElement(doi_element, self.api_qname("links"))
        etree.SubElement(
            links_element,
            self.api_qname("link"),
            attrib={
                "type": "doi",
                "href": f"https://doi.org/{doi}",
            },
        )
        etree.SubElement(
            links_element,
            self.api_qname("link"),
            attrib={
                "type": "altmetric",
                "href": f"https://www.altmetric.com/details.php?doi={doi}",
            },
        )

    def generate_record_xml(self, record):
        """Generate the XML for the record to be created in Symplectic."""
        metadata = record.get("metadata", {})

        import_record_element = etree.Element(
            self.api_qname("import-record"),
            attrib={
                "type-name": "dataset",
                "type-id": SYMPLECTIC_DATASET_TYPE_ID,
            },
            nsmap={"api": self.NAMESPACE_URI},
        )
        native_element = etree.SubElement(
            import_record_element,
            self.api_qname("native"),
        )

        title_element = etree.SubElement(
            native_element,
            self.api_qname("field"),
            attrib={
                "name": "title",
                "type": "text",
                "display-name": "Title",
            },
        )
        title_text_element = etree.SubElement(
            title_element,
            self.api_qname("text"),
        )
        title_text_element.text = metadata.get("title")

        if description := metadata.get("description"):
            abstract_element = etree.SubElement(
                native_element,
                self.api_qname("field"),
                attrib={
                    "name": "abstract",
                    "type": "text",
                    "display-name": "Abstract",
                },
            )
            abstract_text_element = etree.SubElement(
                abstract_element,
                self.api_qname("text"),
            )
            abstract_text_element.text = description

        authors_element = etree.SubElement(
            native_element,
            self.api_qname("field"),
            attrib={
                "name": "authors",
                "type": "person-list",
                "display-name": "Authors/Contributors",
            },
        )
        people_element = etree.SubElement(authors_element, self.api_qname("people"))
        for creator in metadata.get("creators", []):
            po = creator.get("person_or_org", {})
            person_element = etree.SubElement(people_element, self.api_qname("person"))
            last_name_element = etree.SubElement(
                person_element, self.api_qname("last-name")
            )
            last_name_element.text = po.get("family_name")
            first_names_element = etree.SubElement(
                person_element, self.api_qname("first-names")
            )
            first_names_element.text = po.get("given_name")
            # Add ORCID if present
            for identifier in po.get("identifiers", []):
                if identifier.get("scheme") == "orcid":
                    identifiers_element = etree.SubElement(
                        person_element, self.api_qname("identifiers")
                    )
                    orcid_element = etree.SubElement(
                        identifiers_element,
                        self.api_qname("identifier"),
                        attrib=dict(scheme="orcid"),
                    )
                    orcid_element.text = identifier.get("identifier")

        # Licence/Rights
        rights = metadata.get("rights", [])
        if rights:
            licence_element = etree.SubElement(
                native_element,
                self.api_qname("field"),
                attrib={
                    "name": "c-licence",
                    "type": "text",
                    "display-name": "Licence",
                },
            )
            licence_text_element = etree.SubElement(
                licence_element, self.api_qname("text")
            )
            licence_text_element.text = rights[0].get("id")

        doi = record.get("id")
        self.add_doi_subtree(native_element, "c-validated-doi", doi)

        version = metadata.get("version")
        if version:
            version_element = etree.SubElement(
                native_element,
                self.api_qname("field"),
                attrib={
                    "name": "version",
                    "type": "text",
                    "display-name": "Version",
                },
            )
            version_text_element = etree.SubElement(
                version_element, self.api_qname("text")
            )
            version_text_element.text = str(version)

        pub_date = metadata["publication_date"]  # Will raise KeyError if missing
        pub_date_obj = datetime.fromisoformat(pub_date)
        publication_date_element = etree.SubElement(
            native_element,
            self.api_qname("field"),
            attrib={
                "name": "publication-date",
                "type": "date",
                "display-name": "Publication Date",
            },
        )
        publication_date_date_element = etree.SubElement(
            publication_date_element, self.api_qname("date")
        )
        publication_day_element = etree.SubElement(
            publication_date_date_element, self.api_qname("day")
        )
        publication_day_element.text = str(pub_date_obj.day)
        publication_month_element = etree.SubElement(
            publication_date_date_element, self.api_qname("month")
        )
        publication_month_element.text = str(pub_date_obj.month)
        publication_year_element = etree.SubElement(
            publication_date_date_element, self.api_qname("year")
        )
        publication_year_element.text = str(pub_date_obj.year)

        return import_record_element

    def create_record(self, metadata):
        """Create a record in Symplectic Elements."""
        record_xml = self.generate_record_xml(metadata)
        proprietary_id = metadata.get("id")
        url = f"{self.api_url}/publication/records/manual/{proprietary_id}"
        print("URL:", proprietary_id)
        response = requests.put(
            url,
            data=etree.tostring(record_xml, encoding="unicode"),
            headers=self.headers,
        )
        response.raise_for_status()
