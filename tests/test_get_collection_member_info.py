"""Tests for get_collection_member_info.py."""

from copy import deepcopy

import pytest
from ic_data_repo.get_collection_member_info import get_collection_member_info
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service


@pytest.fixture
def record_data():
    """Fixture for record data."""
    return {
        "metadata": {
            "title": "Test Record",
            "description": "This is a test record.",
            "resource_type": {"id": "dataset"},
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "given_name": "Neo",
                        "family_name": "Anderson",
                    }
                }
            ],
            "publication_date": "2026-01-01",
        },
        "access": {
            "record": "public",
            "files": "public",
        },
        "files": {
            "enabled": False,
        },
    }


def test_valid_related_records(db, search_clear, location, vocabularies, record_data):
    """Test for correctness with a collection with valid related records."""
    record_1_data = deepcopy(record_data)
    record_1_data["metadata"]["title"] = "Test Record 1"
    record_1_data["metadata"]["identifiers"] = [
        {"identifier": "10.1234/collection1", "scheme": "doi"},
        {"identifier": "https://example.com/collection1", "scheme": "url"},
    ]
    record_1_draft = records_service.create(system_identity, record_1_data)
    record_1 = records_service.publish(system_identity, record_1_draft.id)

    record_2_data = deepcopy(record_data)
    record_2_data["metadata"]["title"] = "Test Record 2"
    record_2_data["metadata"]["identifiers"] = [
        {"identifier": "10.1234/collection2", "scheme": "doi"},
        {"identifier": "https://example.com/collection2", "scheme": "url"},
    ]
    record_2_draft = records_service.create(system_identity, record_2_data)
    record_2 = records_service.publish(system_identity, record_2_draft.id)

    collection_data = deepcopy(record_data)
    collection_data["metadata"]["related_identifiers"] = [
        {
            "identifier": "10.1234/collection1",
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
        {
            "identifier": "10.1234/collection2",
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    collection_draft = records_service.create(system_identity, collection_data)
    collection = records_service.publish(system_identity, collection_draft.id)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, collection.id)
    result.sort(key=lambda x: x["title"])
    assert len(result) == 2
    assert result[0] == {
        "title": "Test Record 1",
        "url": f"https://127.0.0.1:5000/records/{record_1.id}",
        "dois": ["10.1234/collection1"],
    }
    assert result[1] == {
        "title": "Test Record 2",
        "url": f"https://127.0.0.1:5000/records/{record_2.id}",
        "dois": ["10.1234/collection2"],
    }


# def test_valid_related_draft_records():
#     """Test for correctness with a collection with valid related draft records."""


# Collection with no related records


# Collection with related records but none with relation_type=haspart


# Collection with related records but none with scheme=doi


# Wrong identity (no permission to read the collection)
