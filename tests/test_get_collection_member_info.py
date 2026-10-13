"""Tests for get_collection_member_info.py."""

from flask_principal import AnonymousIdentity
from ic_data_repo.get_collection_member_info import get_collection_member_info
from invenio_access.permissions import any_user, system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service


def _create_doi(draft):
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


def _create_record(mint_doi=True, publish=True, extra_metadata=None):
    """Create a new record."""
    data = {
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
    if extra_metadata:
        data["metadata"].update(extra_metadata)
    draft = records_service.create(system_identity, data)
    if mint_doi:
        draft = _create_doi(draft)
    if publish:
        return records_service.publish(system_identity, draft.id)
    return draft


def _create_new_record_version(record_id, mint_doi=True, publish=True):
    """Create a new version of a record."""
    draft = records_service.new_version(system_identity, record_id)
    if mint_doi:
        draft = _create_doi(draft)
    if publish:
        return records_service.publish(system_identity, draft.id)
    return draft


def test_related_records_valid(db, search_clear, location, vocabularies):
    """Test a collection with valid related records."""
    r1 = _create_record(extra_metadata={"title": "Test Record 1"})
    r2 = _create_record(extra_metadata={"title": "Test Record 2"})
    c = _create_record(
        mint_doi=False,
        extra_metadata={
            "resource_type": {"id": "collection"},
            "related_identifiers": [
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
            ],
        },
    )

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


def test_related_records_anonymous(db, search_clear, location, vocabularies):
    """Test a collection as an anonymous user."""
    r1 = _create_record()
    c = _create_record(
        mint_doi=False,
        extra_metadata={
            "resource_type": {"id": "collection"},
            "related_identifiers": [
                {
                    "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
                    "relation_type": {"id": "haspart"},
                    "scheme": "doi",
                },
            ],
        },
    )

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


def test_related_records_draft(db, search_clear, location, vocabularies):
    """Test that related draft records are ignored."""
    r1_draft = _create_record(publish=False)
    c = _create_record(
        mint_doi=False,
        extra_metadata={
            "resource_type": {"id": "collection"},
            "related_identifiers": [
                {
                    "identifier": r1_draft.data["pids"]["doi"]["identifier"],
                    "relation_type": {"id": "haspart"},
                    "scheme": "doi",
                },
            ],
        },
    )

    # Draft records should be ignored.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_latest_version(db, search_clear, location, vocabularies):
    """Test that only the latest version of related records is returned."""
    r1_v1 = _create_record()
    r1_v2 = _create_new_record_version(r1_v1.id)
    c = _create_record(
        mint_doi=False,
        extra_metadata={
            "resource_type": {"id": "collection"},
            "related_identifiers": [
                {
                    "identifier": r1_v1.data["parent"]["pids"]["doi"]["identifier"],
                    "relation_type": {"id": "haspart"},
                    "scheme": "doi",
                },
            ],
        },
    )

    # Only the latest version of the related record should be returned.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 1

    # The DOI should be the same as the parent DOI for v1 and v2.
    assert result[0]["doi"] == r1_v1.data["parent"]["pids"]["doi"]["identifier"]
    assert result[0]["doi"] == r1_v2.data["parent"]["pids"]["doi"]["identifier"]

    # The URL should point to v2, which is different from v1.
    assert result[0]["url"] != r1_v1.data["links"]["self_html"]
    assert result[0]["url"] == r1_v2.data["links"]["self_html"]


def test_related_records_nonlocal(db, search_clear, location, vocabularies):
    """Test that non-local related records are ignored."""
    c = _create_record(
        mint_doi=False,
        extra_metadata={
            "resource_type": {"id": "collection"},
            "related_identifiers": [
                {
                    "identifier": "10.1234/nonlocal",
                    "relation_type": {"id": "haspart"},
                    "scheme": "doi",
                },
            ],
        },
    )

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_no_haspart(db, search_clear, location, vocabularies):
    """Test that related records without relation_type=haspart are ignored."""
    r1 = _create_record()
    c = _create_record(
        mint_doi=False,
        extra_metadata={
            "resource_type": {"id": "collection"},
            "related_identifiers": [
                {
                    "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
                    "relation_type": {"id": "cites"},
                    "scheme": "doi",
                },
            ],
        },
    )

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_no_doi(db, search_clear, location, vocabularies):
    """Test that related records without scheme=doi are ignored."""
    r1 = _create_record()
    c = _create_record(
        mint_doi=False,
        extra_metadata={
            "resource_type": {"id": "collection"},
            "related_identifiers": [
                {
                    "identifier": r1.data["links"]["self_html"],
                    "relation_type": {"id": "haspart"},
                    "scheme": "url",
                },
            ],
        },
    )

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_restricted(db, search_clear, location, vocabularies, user):
    """Test that restricted related records are ignored without permission."""
    r1_draft = _create_record(publish=False)

    # We need a restricted record. Normally Imperial's schema won't allow that.
    r1_draft._record.access.protection.record = "restricted"
    r1_draft._record.commit()
    db.session.commit()
    r1 = records_service.publish(system_identity, r1_draft.id)
    assert r1.data["access"]["record"] == "restricted"

    c = _create_record(
        mint_doi=False,
        extra_metadata={
            "resource_type": {"id": "collection"},
            "related_identifiers": [
                {
                    "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
                    "relation_type": {"id": "haspart"},
                    "scheme": "doi",
                },
            ],
        },
    )

    # Test identities that do and do not have permission.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 1
    result = get_collection_member_info(user.identity, c.id)
    assert len(result) == 0
