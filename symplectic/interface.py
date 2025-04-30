"""Symplectic API interface."""

import os
import uuid
from datetime import datetime
from functools import partial

import requests
from lxml import etree

API_SUBSCRIPTION_KEY = os.environ["API_SUBSCRIPTION_KEY"]

headers = {
    "Content-Type": "text/xml",
    "Subscription-Key": API_SUBSCRIPTION_KEY,
}
id = uuid.uuid4()

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


record_xml = generate_record_xml(
    title="Very important dataset",
    abstract="This is a very important dataset that contains a lot of information.",
    authors=[
        dict(
            last_name="Cave-Ayland",
            first_names="Christopher",
            orcid="0000-0003-0942-8030",
        )
    ],
    doi="10.1073/pnas.1708252114",
    licence="https://creativecommons.org/licenses/by/4.0/legalcode",
    version="1.0",
    publication_date=datetime.now(),
)

proprietary_id = uuid.uuid4()
response = requests.put(
    BASE_URL + f"publication/records/manual/{str(proprietary_id).upper()}",
    data=etree.tostring(record_xml, encoding="unicode"),
    headers=headers,
)
