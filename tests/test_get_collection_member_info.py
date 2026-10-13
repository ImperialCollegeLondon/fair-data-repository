"""Tests for get_collection_member_info.py."""

from copy import deepcopy

import pytest
from flask_principal import AnonymousIdentity
from ic_data_repo.get_collection_member_info import get_collection_member_info
from invenio_access.permissions import any_user, system_identity
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


def create_doi(draft):
    """Create and reserve a DOI for a draft record."""
    draft = records_service.pids.create(
        system_identity,
        draft.id,
        "doi",
        provider="datacite",
    )
    draft = records_service.pids.reserve(
        system_identity,
        draft.id,
    )
    return draft


def test_related_records_valid(db, search_clear, location, vocabularies, record_data):
    """Test a collection with valid related records."""
    r1_data = deepcopy(record_data)
    r1_data["metadata"]["title"] = "Test Record 1"
    r1_draft = records_service.create(system_identity, r1_data)
    r1_draft = create_doi(r1_draft)
    r1 = records_service.publish(system_identity, r1_draft.id)

    r2_data = deepcopy(record_data)
    r2_data["metadata"]["title"] = "Test Record 2"
    r2_draft = records_service.create(system_identity, r2_data)
    r2_draft = create_doi(r2_draft)
    r2 = records_service.publish(system_identity, r2_draft.id)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
        {
            "identifier": r2.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    result.sort(key=lambda x: x["title"])
    assert len(result) == 2
    assert result[0] == {
        "doi": r1.data["parent"]["pids"]["doi"]["identifier"],
        "url": r1.data["links"]["self_html"],
        "title": r1.data["metadata"]["title"],
    }
    assert result[1] == {
        "doi": r2.data["parent"]["pids"]["doi"]["identifier"],
        "url": r2.data["links"]["self_html"],
        "title": r2.data["metadata"]["title"],
    }


def test_related_records_anonymous(
    db, search_clear, location, vocabularies, record_data
):
    """Test a collection as an anonymous user."""
    r1_data = deepcopy(record_data)
    r1_draft = records_service.create(system_identity, r1_data)
    r1_draft = create_doi(r1_draft)
    r1 = records_service.publish(system_identity, r1_draft.id)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    # Anonymous users should see published records.
    search_clear.indices.refresh()
    identity = AnonymousIdentity()
    identity.provides.add(any_user)
    result = get_collection_member_info(identity, c.id)
    assert len(result) == 1
    assert result[0] == {
        "doi": r1.data["parent"]["pids"]["doi"]["identifier"],
        "url": r1.data["links"]["self_html"],
        "title": r1.data["metadata"]["title"],
    }


def test_related_records_draft(db, search_clear, location, vocabularies, record_data):
    """Test that related draft records are ignored."""
    r1_data = deepcopy(record_data)
    r1_draft = records_service.create(system_identity, r1_data)
    r1_draft = create_doi(r1_draft)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1_draft.data["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    # Draft records should be ignored.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_nonlocal(
    db, search_clear, location, vocabularies, record_data
):
    """Test that non-local related records are ignored."""
    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": "10.1234/nonlocal",
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_no_haspart(
    db, search_clear, location, vocabularies, record_data
):
    """Test that related records without relation_type=haspart are ignored."""
    r1_data = deepcopy(record_data)
    r1_draft = records_service.create(system_identity, r1_data)
    r1_draft = create_doi(r1_draft)
    r1 = records_service.publish(system_identity, r1_draft.id)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "cites"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_no_doi(db, search_clear, location, vocabularies, record_data):
    """Test that related records without scheme=doi are ignored."""
    r1_data = deepcopy(record_data)
    r1_draft = records_service.create(system_identity, r1_data)
    r1_draft = create_doi(r1_draft)
    r1 = records_service.publish(system_identity, r1_draft.id)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["links"]["self_html"],
            "relation_type": {"id": "haspart"},
            "scheme": "url",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_restricted(
    db, search_clear, location, vocabularies, record_data, user
):
    """Test that restricted related records are ignored without permission."""
    r1_data = deepcopy(record_data)
    r1_draft = records_service.create(system_identity, r1_data)
    r1_draft = create_doi(r1_draft)

    # We need a restricted record. Normally Imperial's schema disallows them.
    r1_draft._record.access.protection.record = "restricted"
    r1_draft._record.commit()
    db.session.commit()
    r1 = records_service.publish(system_identity, r1_draft.id)
    assert r1.data["access"]["record"] == "restricted"

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    # Test identities that do and do not have permission.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 1
    result = get_collection_member_info(user.identity, c.id)
    assert len(result) == 0
