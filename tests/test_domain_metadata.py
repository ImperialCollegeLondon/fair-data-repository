"""Tests for domain metadata."""

from contextlib import nullcontext

import pytest
from ic_data_repo.permissions import domain_metadata_action
from invenio_access.permissions import ActionUsers, system_identity
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.resources.serializers.ui import UIJSONSerializer
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_search.proxies import current_search
from marshmallow.exceptions import ValidationError


def _grant_domain_metadata_permission(user_depositor, db):
    """Grant user_depositor the domain-metadata-action permission."""
    db.session.add(ActionUsers.allow(domain_metadata_action, user_id=user_depositor.id))
    db.session.commit()


def _revoke_domain_metadata_permission(user_depositor, db):
    """Revoke a previously-granted domain-metadata-action permission."""
    grant = ActionUsers.query.filter_by(
        action=domain_metadata_action.value, user_id=user_depositor.id
    ).one()
    db.session.delete(grant)
    db.session.commit()


@pytest.mark.parametrize(
    ("entries", "expected_stored", "expected_errors", "publish_outcome"),
    [
        pytest.param(
            [
                {"id": "example-domain-term", "value": "My chosen subject text"},
                {"id": "minimal-domain-term", "value": "A second subject"},
            ],
            [
                {"id": "example-domain-term", "value": "My chosen subject text"},
                {"id": "minimal-domain-term", "value": "A second subject"},
            ],
            [],
            nullcontext(),
            id="valid-pairs",
        ),
        pytest.param(
            [{"id": "does-not-exist", "value": "Some subject"}],
            [{"value": "Some subject"}],
            ["custom_fields.imperial:domain_metadata.0.id"],
            pytest.raises(ValidationError),
            id="unknown-id",
        ),
        pytest.param(
            [{"value": "Some subject"}],
            [{"value": "Some subject"}],
            ["custom_fields.imperial:domain_metadata.0.id"],
            pytest.raises(ValidationError),
            id="missing-id",
        ),
        pytest.param(
            [{"id": "example-domain-term", "value": ""}],
            [{"id": "example-domain-term"}],
            ["custom_fields.imperial:domain_metadata.0.value"],
            pytest.raises(ValidationError),
            id="blank-value",
        ),
        pytest.param(
            [{"id": "example-domain-term"}],
            [{"id": "example-domain-term"}],
            ["custom_fields.imperial:domain_metadata.0.value"],
            pytest.raises(ValidationError),
            id="missing-value",
        ),
    ],
)
def test_domain_metadata_custom_field(
    vocabularies,
    icl_community,
    user_depositor,
    metadata,
    entries,
    expected_stored,
    expected_errors,
    publish_outcome,
    db,
):
    """imperial:domain_metadata: persistence and validation.

    Multiple {id, value} pairs, each referencing a different vocabulary
    term, persist independently and round-trip exactly as {id, value} - no
    vocabulary properties (title, props, etc.) are ever copied onto the
    record. An unknown id, or a blank/missing value, is flagged rather than
    silently stored as if valid.

    Drafts may be saved with validation errors (so work-in-progress can be
    saved incomplete) - the API surfaces this as a non-blocking `errors`
    entry on an otherwise-fine response, rather than a hard rejection on
    create. Strict validation only happens at publish time - checked here
    for the invalid cases only (`publish_status` is None for valid-pairs,
    since actually succeeding at publish also requires a community
    submission unrelated to domain_metadata; the draft-level checks above
    already prove domain_metadata itself raises no error for valid input).
    """
    _grant_domain_metadata_permission(user_depositor, db)
    record_data = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {"imperial:domain_metadata": entries},
    }
    record = current_rdm_records_service.create(user_depositor.identity, record_data)
    assert record["status"] == "draft_with_review"

    error_fields = [e["field"] for e in record.errors]
    assert sorted(error_fields) == sorted(expected_errors)

    stored_entries = record["custom_fields"].get("imperial:domain_metadata", [])
    assert stored_entries == expected_stored

    # Delete auto-created review for easier testing.
    current_rdm_records_service.review.delete(system_identity, record.id)

    # Publishing with invalid fields raises ValidationError.
    with publish_outcome:
        current_rdm_records_service.publish(system_identity, record.id)


def test_domain_metadata_custom_field_search(
    vocabularies, icl_community, user_depositor, metadata, db
):
    """imperial:domain_metadata: findable via the default free-text search.

    Both the ``id`` and ``value`` of a domain metadata entry are analysed and
    included in the OpenSearch mapping (see ``DomainMetadataCF.mapping``),
    so a plain ``q=`` search picks up either. A second, unrelated record
    (with no domain metadata at all) is created alongside to prove the
    match is actually driven by the custom field's content rather than
    every record matching every query.
    """
    _grant_domain_metadata_permission(user_depositor, db)
    with_domain_metadata = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [
                {"id": "example-domain-term", "value": "Zebra unicorn quokka"}
            ]
        },
    }
    without_domain_metadata = {
        "metadata": {**metadata, "title": "Unrelated other record"},
        "files": {"enabled": False},
    }

    matching_record = current_rdm_records_service.create(
        user_depositor.identity, with_domain_metadata
    )
    assert matching_record["status"] == "draft_with_review"

    other_record = current_rdm_records_service.create(
        user_depositor.identity, without_domain_metadata
    )
    assert other_record["status"] == "draft_with_review"

    current_search.flush_and_refresh("*")

    # matches on the entry's "value" (a word unique to this test) and finds
    # only this record, since nothing else in the suite uses it ...
    for q in ("quokka", "unicorn"):
        result = current_rdm_records_service.search_drafts(
            user_depositor.identity, params={"q": q}
        )
        hit_ids = [hit["id"] for hit in result]
        assert hit_ids == [matching_record["id"]]

    # ... and on the entry's "id" -- other tests' records may share this
    # vocabulary id, so only assert this record is among the matches (and
    # that the record with no domain metadata at all is not).
    result = current_rdm_records_service.search_drafts(
        user_depositor.identity, params={"q": "example-domain-term"}
    )
    hit_ids = [hit["id"] for hit in result]
    assert matching_record["id"] in hit_ids
    assert other_record["id"] not in hit_ids

    # a term present in neither record matches nothing.
    result = current_rdm_records_service.search_drafts(
        user_depositor.identity, params={"q": "qwertyxyz999"}
    )
    assert list(result) == []

    # sanity check: both records are otherwise listed (proves the filtering
    # above is the query doing its job, not the other record being hidden).
    result = current_rdm_records_service.search_drafts(
        user_depositor.identity, params={}
    )
    hit_ids = [hit["id"] for hit in result]
    assert matching_record["id"] in hit_ids
    assert other_record["id"] in hit_ids


def test_domain_metadata_landing_page_shows_resolved_vocabulary(
    vocabularies, icl_community, user_depositor, metadata, db
):
    """imperial:domain_metadata: landing-page (UI) display resolves terms."""
    _grant_domain_metadata_permission(user_depositor, db)
    record_data = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [
                {"id": "example-domain-term", "value": "Full props term"},
                {"id": "minimal-domain-term", "value": "Minimal term"},
            ]
        },
    }
    record = current_rdm_records_service.create(user_depositor.identity, record_data)
    assert record["status"] == "draft_with_review"

    # Use the UI serializer to get the record format expected by the landing page.
    record_ui = UIJSONSerializer().dump_obj(record.to_dict())

    entries = record_ui["ui"]["custom_fields"]["imperial:domain_metadata"]
    assert entries == [
        {
            "id": "example-domain-term",
            "value": "Full props term",
            "title": "Example domain term",
            "props": {
                "subjectScheme": "Example Scheme",
                "schemeURI": "https://example.org/schemes/example-scheme",
                "valueURI": "https://example.org/schemes/example-scheme/example-domain-term",
            },
        },
        {
            "id": "minimal-domain-term",
            "value": "Minimal term",
            "title": "Minimal domain term",
            "props": {"subjectScheme": None, "schemeURI": None, "valueURI": None},
        },
    ]


def test_domain_metadata_absent_from_landing_page_ui_when_not_set(
    vocabularies, icl_community, user_depositor, metadata
):
    """imperial:domain_metadata: absent from the landing-page UI when unset."""
    record = current_rdm_records_service.create(
        user_depositor.identity, {"metadata": metadata, "files": {"enabled": False}}
    )
    assert record["status"] == "draft_with_review"

    # Use the UI serializer to get the record format expected by the landing page.
    record_ui = UIJSONSerializer().dump_obj(record.to_dict())

    assert "imperial:domain_metadata" not in record_ui["ui"]["custom_fields"]


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_domain_metadata_create_requires_permission(
    grant, outcome, vocabularies, icl_community, user_depositor, metadata, db
):
    """imperial:domain_metadata: create is gated by the permission."""
    if grant:
        _grant_domain_metadata_permission(user_depositor, db)

    record_data = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "v1"}]
        },
    }

    # Raises PermissionDeniedError if not granted permission.
    with outcome:
        result = current_rdm_records_service.create(
            user_depositor.identity, record_data
        )
        assert result["custom_fields"]["imperial:domain_metadata"] == [
            {"id": "example-domain-term", "value": "v1"}
        ]


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_domain_metadata_add_requires_permission(
    grant, outcome, vocabularies, icl_community, user_depositor, metadata, db
):
    """imperial:domain_metadata: adding it later is gated by the permission."""
    plain = current_rdm_records_service.create(
        user_depositor.identity, {"metadata": metadata, "files": {"enabled": False}}
    )
    assert plain["status"] == "draft_with_review"

    if grant:
        _grant_domain_metadata_permission(user_depositor, db)

    update_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "v1"}]
        },
    }

    # Raises PermissionDeniedError if not granted permission.
    with outcome:
        result = current_rdm_records_service.update_draft(
            user_depositor.identity, plain.id, update_json
        )
        assert result["custom_fields"]["imperial:domain_metadata"] == [
            {"id": "example-domain-term", "value": "v1"}
        ]


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_domain_metadata_reorder_requires_permission(
    grant, outcome, vocabularies, icl_community, user_depositor, metadata, db
):
    """imperial:domain_metadata: reordering entries is gated by the permission."""
    _grant_domain_metadata_permission(user_depositor, db)
    original_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [
                {"id": "example-domain-term", "value": "A"},
                {"id": "minimal-domain-term", "value": "B"},
            ]
        },
    }
    created = current_rdm_records_service.create(user_depositor.identity, original_json)
    assert created["status"] == "draft_with_review"

    if not grant:
        _revoke_domain_metadata_permission(user_depositor, db)

    reordered_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [
                {"id": "minimal-domain-term", "value": "B"},
                {"id": "example-domain-term", "value": "A"},
            ]
        },
    }

    # Raises PermissionDeniedError if not granted permission.
    with outcome:
        result = current_rdm_records_service.update_draft(
            user_depositor.identity, created.id, reordered_json
        )
        assert result["custom_fields"]["imperial:domain_metadata"] == [
            {"id": "minimal-domain-term", "value": "B"},
            {"id": "example-domain-term", "value": "A"},
        ]


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_domain_metadata_removal_requires_permission(
    grant, outcome, vocabularies, icl_community, user_depositor, metadata, db
):
    """imperial:domain_metadata: removing all entries is gated by the permission."""
    _grant_domain_metadata_permission(user_depositor, db)
    original_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "A"}]
        },
    }
    created = current_rdm_records_service.create(user_depositor.identity, original_json)
    assert created["status"] == "draft_with_review"

    if not grant:
        _revoke_domain_metadata_permission(user_depositor, db)

    removal_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {"imperial:domain_metadata": []},
    }

    # Raises PermissionDeniedError if not granted permission.
    with outcome:
        result = current_rdm_records_service.update_draft(
            user_depositor.identity, created.id, removal_json
        )
        assert result["custom_fields"].get("imperial:domain_metadata", []) == []


@pytest.mark.parametrize(
    ("grant", "outcome"),
    [(True, nullcontext()), (False, pytest.raises(PermissionDeniedError))],
)
def test_domain_metadata_unchanged_update_requires_permission(
    grant, outcome, vocabularies, icl_community, user_depositor, metadata, db
):
    """imperial:domain_metadata: resubmitting it unchanged is still gated."""
    _grant_domain_metadata_permission(user_depositor, db)
    original_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "A"}]
        },
    }
    created = current_rdm_records_service.create(user_depositor.identity, original_json)
    assert created["status"] == "draft_with_review"

    if not grant:
        _revoke_domain_metadata_permission(user_depositor, db)

    unchanged_json = {
        "metadata": {**metadata, "title": "Updated title, domain metadata untouched"},
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "A"}]
        },
    }

    # Raises PermissionDeniedError if not granted permission.
    with outcome:
        current_rdm_records_service.update_draft(
            user_depositor.identity, created.id, unchanged_json
        )
