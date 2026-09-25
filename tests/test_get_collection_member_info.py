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


def test_valid_related_records(db, search_clear, location, vocabularies, record_data):
    """Test a collection with valid related records."""
    r_1_data = deepcopy(record_data)
    r_1_data["metadata"]["title"] = "Test Record 1"
    r_1_draft = records_service.create(system_identity, r_1_data)
    r_1_draft = create_doi(r_1_draft)
    r_1 = records_service.publish(system_identity, r_1_draft.id)

    r_2_data = deepcopy(record_data)
    r_2_data["metadata"]["title"] = "Test Record 2"
    r_2_draft = records_service.create(system_identity, r_2_data)
    r_2_draft = create_doi(r_2_draft)
    r_2 = records_service.publish(system_identity, r_2_draft.id)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r_1.data["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
        {
            "identifier": r_2.data["pids"]["doi"]["identifier"],
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
        "title": r_1.data["metadata"]["title"],
        "url": r_1.data["links"]["self_html"],
        "doi": r_1.data["pids"]["doi"]["identifier"],
    }
    assert result[1] == {
        "title": r_2.data["metadata"]["title"],
        "url": r_2.data["links"]["self_html"],
        "doi": r_2.data["pids"]["doi"]["identifier"],
    }


def test_valid_related_draft_records(
    db, search_clear, location, vocabularies, record_data
):
    """Test a collection with valid related draft records."""
    r_1_data = deepcopy(record_data)
    r_1_draft = records_service.create(system_identity, r_1_data)
    r_1_draft = create_doi(r_1_draft)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r_1_draft.data["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 1
    assert result[0] == {
        "title": r_1_draft.data["metadata"]["title"],
        "url": r_1_draft.data["links"]["self_html"],
        "doi": r_1_draft.data["pids"]["doi"]["identifier"],
    }


def test_nonlocal_related_records(
    db, search_clear, location, vocabularies, record_data
):
    """Test a collection with no locally-hosted related records."""
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
    """Test a collection with related records without relation_type=haspart."""
    r_1_data = deepcopy(record_data)
    r_1_draft = records_service.create(system_identity, r_1_data)
    r_1_draft = create_doi(r_1_draft)
    r_1 = records_service.publish(system_identity, r_1_draft.id)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r_1.data["pids"]["doi"]["identifier"],
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
    """Test a collection with related records without scheme=doi."""
    r_1_data = deepcopy(record_data)
    r_1_draft = records_service.create(system_identity, r_1_data)
    r_1_draft = create_doi(r_1_draft)
    r_1 = records_service.publish(system_identity, r_1_draft.id)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r_1.data["links"]["self_html"],
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
    db, search_clear, location, vocabularies, user, record_data
):
    """Test restricted related records without permission."""
    r_1_data = deepcopy(record_data)
    r_1_draft = records_service.create(system_identity, r_1_data)
    r_1_draft = create_doi(r_1_draft)

    # We need a restricted record. Normally Imperial's schema disallows them.
    r_1_draft._record.access.protection.record = "restricted"
    r_1_draft._record.commit()
    db.session.commit()
    r_1 = records_service.publish(system_identity, r_1_draft.id)
    assert r_1.data["access"]["record"] == "restricted"

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r_1.data["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    # Use a different identity that does not have permission.
    search_clear.indices.refresh()
    result = get_collection_member_info(user.identity, c.id)
    assert len(result) == 0


def test_related_records_anonymous_user(
    db, search_clear, location, vocabularies, record_data
):
    """Test a collection as an anonymous user."""
    r_1_data = deepcopy(record_data)
    r_1_draft = records_service.create(system_identity, r_1_data)
    r_1_draft = create_doi(r_1_draft)
    r_1 = records_service.publish(system_identity, r_1_draft.id)

    r_2_data = deepcopy(record_data)
    r_2_draft = records_service.create(system_identity, r_2_data)
    r_2_draft = create_doi(r_2_draft)

    c_data = deepcopy(record_data)
    c_data["metadata"]["resource_type"]["id"] = "collection"
    c_data["metadata"]["related_identifiers"] = [
        {
            "identifier": r_1.data["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
        {
            "identifier": r_2_draft.data["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    c_draft = records_service.create(system_identity, c_data)
    c = records_service.publish(system_identity, c_draft.id)

    # Anonymous users should see published records, but not drafts.
    search_clear.indices.refresh()
    identity = AnonymousIdentity()
    identity.provides.add(any_user)
    result = get_collection_member_info(identity, c.id)
    assert len(result) == 1
    assert result[0] == {
        "title": r_1.data["metadata"]["title"],
        "url": r_1.data["links"]["self_html"],
        "doi": r_1.data["pids"]["doi"]["identifier"],
    }
