"""Symplectic API client for creating records in Symplectic Elements."""

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

    def __init__(self, api_url, api_key):
        """Initialize the Symplectic client."""
        self.api_url = api_url
        self.api_key = api_key
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

    def generate_record_xml(self, record, datacite_prefix):
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

        # Add c-validated-doi field if a DOI is present
        doi = f"10.0590/{record.get('id')}"

        self.add_doi_subtree(native_element, "c-validated-doi", doi)

        # Add c-related-doi fields for each DOI in related_identifiers
        for identifier in metadata.get("related_identifiers", []):
            relation_type = identifier.get("relation_type", {})
            if (
                relation_type.get("id") == "ispublishedin"
                and identifier.get("scheme") == "doi"
            ):
                related_doi_element = etree.SubElement(
                    native_element,
                    self.api_qname("field"),
                    attrib={
                        "name": "c-related-doi",
                        "type": "text",
                        "display-name": "DOI of related publication",
                    },
                )
                related_doi_text = etree.SubElement(
                    related_doi_element, self.api_qname("text")
                )
                related_doi_text.text = identifier.get("identifier")

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

    def create_record(self, metadata, datacite_prefix):
        """Create a record in Symplectic Elements."""
        record_xml = self.generate_record_xml(metadata, datacite_prefix)

        proprietary_id = metadata.get("id")
        url = f"{self.api_url}/publication/records/manual/{proprietary_id}"
        response = requests.put(
            url,
            data=etree.tostring(record_xml, encoding="unicode"),
            headers=self.headers,
        )
        response.raise_for_status()

        root = etree.fromstring(response.content)
        ns = {"api": "http://www.symplectic.co.uk/publications/api"}

        # Extract <api:object> id
        object_elem = root.find(".//api:object", namespaces=ns)
        object_id = object_elem.get("id") if object_elem is not None else None

        # Extract all <api:text> for fields named c-related-doi
        related_doi_text = []
        for field in root.findall(".//api:field[@name='c-related-doi']", namespaces=ns):
            text_elem = field.find("api:text", namespaces=ns)
            if text_elem is not None and text_elem.text:
                related_doi_text.append(text_elem.text)

        # Fetch related object IDs
        related_object_id = self.fetch_related_objects(related_doi_text)
        if related_object_id:
            self.link_related_records(object_id, related_object_id)

        return object_id, related_doi_text, related_object_id

    def fetch_related_objects(self, related_doi_texts):
        """Search for object_ids to link to based on related DOIs."""
        for doi in related_doi_texts:
            url = f'{self.api_url}/publications?detail=single-record&query=doi="{doi}"'
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            root = etree.fromstring(response.content)
            ns = {"api": "http://www.symplectic.co.uk/publications/api"}

            object_elem = root.find(".//api:object", namespaces=ns)
            related_object_id = (
                object_elem.get("id") if object_elem is not None else None
            )

            if related_object_id:
                return related_object_id

        return None

    def link_related_records(self, from_object_id, to_object_id):
        """Link related records using the object IDs from the responses from the API."""
        ns = "http://www.symplectic.co.uk/publications/api"
        root = etree.Element("import-relationship", xmlns=ns)
        etree.SubElement(root, "from-object").text = f"publication({from_object_id})"
        etree.SubElement(root, "to-object").text = f"publication({to_object_id})"
        etree.SubElement(root, "type-id").text = "1"

        xml_data = etree.tostring(root, encoding="unicode", pretty_print=True)

        url = f"{self.api_url}/relationships"
        response = requests.post(
            url,
            data=xml_data,
            headers=self.headers,
        )
        response.raise_for_status()
        return response
