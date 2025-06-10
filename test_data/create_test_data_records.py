"""Script to upload realistic test datasets for the Imperial FAIR Data repository.

usage: pipenv run python create_test_data_records.py COMMUNITY_ID

The COMMUNITY_ID specifies a pre-existing community that the new records are created in.

Make sure you've started the Invenio services have been setup and are running. Should be
run in the `test_data` directory. Assumes you've already run the `download_test_data`
script and (meta)data is stored in the working directory under the expected directory
structure.

Does the following:

- Checks the community specified exists.
- Finds all files matching the glob `*/metadata.json`.
- For each file:
  - Reads in the metadata in Datacite json format.
  - Creates a draft record by converting the Datacite metadata to the repository schema.
  - Uploads the files associated with the dataset to the draft record.
  - Publishes the record.
  - Creates a community inclusion request.
  - Accepts the record into the community.
"""

import base64
import json
import re
import string
import sys
from pathlib import Path
import random

from faker import Faker
from invenio_access.permissions import system_identity
from invenio_app.factory import create_app
from invenio_communities.proxies import current_communities
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_rdm_records.proxies import (
    current_rdm_records_service,
    current_record_communities_service,
)
from invenio_requests.proxies import current_requests_service

FILE_URI_REGEX = re.compile(
    "https://data.hpc.imperial.ac.uk/resolve/\\?doi=\\d+\\&file=\\d+"
)
"""Regex to check if a related identifier refers to a data file."""

IMPERIAL_COLLEGE_ROR = "041kmwe10"
"""ROR persistent identifier for Imperial College."""


def get_filename_from_scheme_uri(uri):
    """Get filename from b64 encoded URI."""
    encoded = uri.lstrip("filename://")
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")


def get_orcid_from_person_metadata(metadata):
    """Get orcid value from creator/contributor metadata."""
    return metadata["nameIdentifiers"][0]["nameIdentifier"].lstrip("https://orcid.org/")


def datacite_to_invenio_schema(datacite):
    """Convert datacite schema metadata to internal Invenio RDM Record schema."""
    data = datacite["data"]["attributes"]
    creator = data["creators"][0]
    title = data["titles"][0]["title"]
    pub_date = data["published"]
    author = {
        "person_or_org": {
            "family_name": creator["familyName"],
            "given_name": creator["givenName"],
            "type": "personal",
            "identifiers": [
                {
                    "scheme": "orcid",
                    "identifier": get_orcid_from_person_metadata(creator),
                }
            ],
        },
        "role": {"id": "researcher"},
        "affiliations": [{"id": IMPERIAL_COLLEGE_ROR}],
    }
    version = data["version"]
    description = data["descriptions"][0]["description"]
    related_identifiers = [
        ri
        for ri in data["relatedIdentifiers"]
        if not FILE_URI_REGEX.match(ri.get("relatedIdentifier", ""))
        and not ri.get("relatedMetadataScheme") == "ORE"
    ]

    dart_id = ''.join(
        random.choice(string.ascii_letters + string.digits)
        for _ in range(random.randint(1, 100))
    )

    return {
        "access": {
            "record": "public",
            "files": "public",
        },
        "files": {
            "enabled": True,
        },
        "pids": {},
        "metadata": {
            "resource_type": {"id": "dataset"},
            "creators": [author],
            "title": title,
            "publisher": "Imperial College London",
            "publication_date": pub_date,
            "subjects": [],
            "contributors": [
                {
                    "person_or_org": {
                        "name": "Imperial College London",
                        "type": "organizational",
                    },
                    "role": {"id": "hostinginstitution"},
                },
                {
                    "person_or_org": {
                        "name": "Imperial College London Research Computing Service",
                        "type": "organizational",
                    },
                    "role": {"id": "datamanager"},
                },
            ]
            + [
                {
                    "person_or_org": {
                        "family_name": contributor["familyName"],
                        "given_name": contributor["givenName"],
                        "type": "personal",
                        "identifiers": [
                            {
                                "scheme": "orcid",
                                "identifier": get_orcid_from_person_metadata(
                                    contributor
                                ),
                            }
                        ],
                    },
                    "role": {"id": "researcher"},
                    "affiliations": [],
                }
                for contributor in data["contributors"][3:]
            ],
            "languages": [],
            "related_identifiers": [
                {
                    "identifier": ri["relatedIdentifier"],
                    "scheme": ri["relatedIdentifierType"].lower(),
                    "relation_type": dict(id=ri["relationType"].lower()),
                }
                for ri in related_identifiers
            ],
            "sizes": [],
            "formats": [],
            "version": version,
            "description": description,
            "additional_descriptions": [],
            "funding": [],
            "references": [],
            "identifiers": [],
            "dates": [
                {
                    "date": date_meta["date"],
                    "type": {"id": date_meta["dateType"].lower()},
                }
                for date_meta in data["dates"]
            ],
            "rights": [
                {
                    "id": rights_meta.get("rightsIdentifier", "cc0-1.0").lower(),
                }
                for rights_meta in data["rightsList"]
            ],
        },
        "custom_fields": {"imperial:dart_id": dart_id},
    }


def create_draft_record(datacite, identity):
    """Create a draft RDM Record from `datacite` metadata owned by `identity`."""
    return current_rdm_records_service.create(
        data=datacite_to_invenio_schema(datacite), identity=identity
    )


def add_files_to_draft(draft, datacite, identity, dir_path):
    """Upload files to draft record.

    File names and order are extracted from the Datacite metadata from related
    identifier entries with a 'schemaUri' value that match `FILE_URI_REGEX`.
    """
    draft_file_service = current_rdm_records_service.draft_files
    file_data = [
        {"key": get_filename_from_scheme_uri(ri["schemeUri"])}
        for ri in datacite["data"]["attributes"]["relatedIdentifiers"]
        if FILE_URI_REGEX.match(ri["relatedIdentifier"])
    ]
    draft_file_service.init_files(identity, draft.id, data=file_data)
    for fd in file_data:
        filename = fd["key"]
        with open(dir_path / filename, "rb") as f:
            draft_file_service.set_file_content(identity, draft.id, filename, f)
        draft_file_service.commit_file(identity, draft.id, filename)


if __name__ == "__main__":
    try:
        community_id = sys.argv[1]
    except IndexError:
        raise ValueError(
            "You must provide a community identifier as a command line argument."
        )

    paths = Path(".").glob("*/metadata.json")
    fake = Faker()
    app = create_app()
    with app.app_context():
        try:
            current_communities.service.read(system_identity, id_=community_id).data
        except PIDDoesNotExistError:
            raise ValueError(f"Could not find community with id - '{community_id}'")

        for path in paths:
            with path.open() as f:
                datacite = json.load(f)

            draft = create_draft_record(datacite, system_identity)

            add_files_to_draft(draft, datacite, system_identity, path.parent)

            # make public
            record = current_rdm_records_service.publish(
                id_=draft.id, identity=system_identity
            )
            request_id = current_record_communities_service.add(
                system_identity,
                record.id,
                dict(communities=[dict(id=community_id, require_review=False)]),
            )[0][0]["request_id"]

            current_requests_service.execute_action(
                system_identity, request_id, "accept"
            )
