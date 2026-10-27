"""Tests for get_collection_member_info.py."""

from flask_principal import AnonymousIdentity
from ic_data_repo.get_collection_member_info import get_collection_member_info
from invenio_access.permissions import any_user, system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service


def test_related_records_valid(record_tester, search_clear):
    """Test a collection with valid related records."""
    record_tester.data["metadata"]["title"] = "Test Record 1"
    record_tester.create()
    record_tester.create_doi()
    r1 = record_tester.publish(identity=system_identity)

    record_tester.data["metadata"]["title"] = "Test Record 2"
    record_tester.create()
    record_tester.create_doi()
    r2 = record_tester.publish(identity=system_identity)

    record_tester.data["metadata"]["title"] = "Test Collection"
    record_tester.data["metadata"]["resource_type"] = {"id": "collection"}
    record_tester.data["metadata"]["related_identifiers"] = [
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
    record_tester.create()
    c = record_tester.publish(identity=system_identity)

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


def test_related_records_latest_version(record_tester, search_clear):
    """Test that only the latest version of related records is returned."""
    record_tester.create()
    record_tester.create_doi()
    r1_v1 = record_tester.publish(identity=system_identity)

    record_tester.new_version()
    record_tester.create_doi()
    r1_v2 = record_tester.publish(identity=system_identity)

    record_tester.data["metadata"]["resource_type"] = {"id": "collection"}
    record_tester.data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1_v1.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    record_tester.create()
    c = record_tester.publish(identity=system_identity)

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


def test_related_records_nonlocal(record_tester, search_clear):
    """Test that non-local related records are ignored."""
    record_tester.data["metadata"]["resource_type"] = {"id": "collection"}
    record_tester.data["metadata"]["related_identifiers"] = [
        {
            "identifier": "10.1234/nonlocal",
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    record_tester.create()
    c = record_tester.publish(identity=system_identity)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_no_haspart(record_tester, search_clear):
    """Test that related records without relation_type=haspart are ignored."""
    record_tester.create()
    record_tester.create_doi()
    r1 = record_tester.publish(identity=system_identity)

    record_tester.data["metadata"]["resource_type"] = {"id": "collection"}
    record_tester.data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "cites"},
            "scheme": "doi",
        },
    ]
    record_tester.create()
    c = record_tester.publish(identity=system_identity)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_no_doi(record_tester, search_clear):
    """Test that related records without scheme=doi are ignored."""
    record_tester.create()
    record_tester.create_doi()
    r1 = record_tester.publish(identity=system_identity)

    record_tester.data["metadata"]["resource_type"] = {"id": "collection"}
    record_tester.data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["links"]["self_html"],
            "relation_type": {"id": "haspart"},
            "scheme": "url",
        },
    ]
    record_tester.create()
    c = record_tester.publish(identity=system_identity)

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_anonymous(record_tester, search_clear):
    """Test a collection as an anonymous user."""
    record_tester.create()
    record_tester.create_doi()
    r1 = record_tester.publish(identity=system_identity)

    record_tester.data["metadata"]["resource_type"] = {"id": "collection"}
    record_tester.data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    record_tester.create()
    c = record_tester.publish(identity=system_identity)

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


def test_related_records_draft(record_tester, search_clear):
    """Test that related draft records are ignored."""
    record_tester.create()
    r1_draft = record_tester.create_doi()

    record_tester.data["metadata"]["resource_type"] = {"id": "collection"}
    record_tester.data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1_draft.data["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    record_tester.create()
    c = record_tester.publish(identity=system_identity)

    # Draft records should be ignored.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_restricted(record_tester, search_clear, db, user):
    """Test that restricted related records are ignored without permission."""
    record_tester.create(identity=system_identity)
    r1_draft = record_tester.create_doi(identity=system_identity)

    # Here be dragons: Imperial normally disallows restricted records.
    # Reserve explicitly so Invenio does not discard the new DOI when we force
    # the record to restricted before publication.
    records_service.pids.reserve(system_identity, r1_draft.id)
    r1_draft._record.access.protection.record = "restricted"
    r1_draft._record.commit()
    db.session.commit()
    r1 = record_tester.publish(identity=system_identity)
    assert r1.data["access"]["record"] == "restricted"

    record_tester.data["metadata"]["resource_type"] = {"id": "collection"}
    record_tester.data["metadata"]["related_identifiers"] = [
        {
            "identifier": r1.data["parent"]["pids"]["doi"]["identifier"],
            "relation_type": {"id": "haspart"},
            "scheme": "doi",
        },
    ]
    record_tester.create()
    c = record_tester.publish(identity=system_identity)

    # Test identities that do and do not have permission.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 1
    result = get_collection_member_info(user.identity, c.id)
    assert len(result) == 0
