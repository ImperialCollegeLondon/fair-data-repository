"""Tests for get_collection_member_info.py."""

from copy import deepcopy

import pytest
from flask_principal import AnonymousIdentity
from ic_data_repo.get_collection_member_info import get_collection_member_info
from invenio_access.permissions import any_user, system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service


@pytest.fixture
def records(record_tester):
    """Factory to create related records."""

    class _Records:
        def __init__(self):
            self.tester = deepcopy(record_tester)
            self.count = 0

        def create(self, new_version=False, publish=True):
            if new_version:
                self.tester.new_version()
            else:
                self.count += 1
                self.tester.data["metadata"]["title"] = f"Test Record {self.count}"
                self.tester.create()
            draft = self.tester.create_doi()
            return self.tester.publish(identity=system_identity) if publish else draft

    return _Records()


@pytest.fixture
def collections(record_tester):
    """Factory to create collections of related records."""

    class _Collections:
        def __init__(self):
            self.tester = deepcopy(record_tester)
            self.tester.data["metadata"]["title"] = "Test Collection"
            self.tester.data["metadata"]["resource_type"] = {"id": "collection"}
            self.tester.data["metadata"]["related_identifiers"] = []

        def add(self, identifier, relation_type, scheme):
            self.tester.data["metadata"]["related_identifiers"].append(
                {
                    "identifier": identifier,
                    "relation_type": {"id": relation_type},
                    "scheme": scheme,
                }
            )

        def create(self):
            self.tester.create()
            return self.tester.publish(identity=system_identity)

    return _Collections()


def test_related_records_valid(records, collections, search_clear):
    """Test a collection with valid related records."""
    r1 = records.create()
    r2 = records.create()

    collections.add(r1.data["parent"]["pids"]["doi"]["identifier"], "haspart", "doi")
    collections.add(r2.data["parent"]["pids"]["doi"]["identifier"], "haspart", "doi")
    c = collections.create()

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


def test_related_records_latest_version(records, collections, search_clear):
    """Test that only the latest version of related records is returned."""
    r1_v1 = records.create()
    r1_v2 = records.create(new_version=True)

    collections.add(r1_v1.data["parent"]["pids"]["doi"]["identifier"], "haspart", "doi")
    c = collections.create()

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


def test_related_records_nonlocal(collections, search_clear):
    """Test that non-local related records are ignored."""
    collections.add("10.1234/nonlocal", "haspart", "doi")
    c = collections.create()

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_no_haspart(records, collections, search_clear):
    """Test that related records without relation_type=haspart are ignored."""
    r1 = records.create()

    collections.add(r1.data["parent"]["pids"]["doi"]["identifier"], "cites", "doi")
    c = collections.create()

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_no_doi(records, collections, search_clear):
    """Test that related records without scheme=doi are ignored."""
    r1 = records.create()

    collections.add(r1.data["links"]["self_html"], "haspart", "url")
    c = collections.create()

    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_anonymous(records, collections, search_clear):
    """Test a collection as an anonymous user."""
    r1 = records.create()

    collections.add(r1.data["parent"]["pids"]["doi"]["identifier"], "haspart", "doi")
    c = collections.create()

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


def test_related_records_draft(records, collections, search_clear):
    """Test that related draft records are ignored."""
    r1_draft = records.create(publish=False)

    collections.add(r1_draft.data["pids"]["doi"]["identifier"], "haspart", "doi")
    c = collections.create()

    # Draft records should be ignored.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 0


def test_related_records_restricted(record_tester, collections, search_clear, db, user):
    """Test that restricted related records are ignored without permission."""
    record_tester.create(identity=system_identity)
    r1_draft = record_tester.create_doi(identity=system_identity)
    # Here be dragons: Imperial normally disallows restricted records. Reserve the DOI
    # explicitly so Invenio does not discard it when we force the record to restricted
    # before publication.
    records_service.pids.reserve(system_identity, r1_draft.id)
    r1_draft._record.access.protection.record = "restricted"
    r1_draft._record.commit()
    db.session.commit()
    r1 = record_tester.publish(identity=system_identity)
    assert r1.data["access"]["record"] == "restricted"

    collections.add(r1.data["parent"]["pids"]["doi"]["identifier"], "haspart", "doi")
    c = collections.create()

    # Test identities that do and do not have permission.
    search_clear.indices.refresh()
    result = get_collection_member_info(system_identity, c.id)
    assert len(result) == 1
    result = get_collection_member_info(user.identity, c.id)
    assert len(result) == 0
