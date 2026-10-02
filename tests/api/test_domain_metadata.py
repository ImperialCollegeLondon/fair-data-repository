"""Tests for domain metadata."""

import pytest
from ic_data_repo.permissions import domain_metadata_action
from invenio_access.permissions import ActionUsers
from invenio_search.proxies import current_search


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


def _csrf_headers(client, api_headers):
    """api_headers plus the X-CSRFToken header PUT/DELETE need.

    Read from the csrftoken cookie set by an earlier write request in this
    same client session (see invenio_rest.csrf) - required for PUT even
    though the create endpoint doesn't seem to need it, since it's
    exercised for the first time by these tests (see
    test_domain_metadata_update_requires_permission's module-level
    docstring note below).
    """
    cookie = client.get_cookie("csrftoken")
    return {**api_headers, "X-CSRFToken": cookie.value if cookie else ""}


@pytest.mark.parametrize(
    ("entries", "expected_stored", "expected_errors", "publish_status"),
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
            None,
            id="valid-pairs",
        ),
        pytest.param(
            [{"id": "does-not-exist", "value": "Some subject"}],
            [{"value": "Some subject"}],
            ["custom_fields.imperial:domain_metadata.0.id"],
            400,
            id="unknown-id",
        ),
        pytest.param(
            [{"value": "Some subject"}],
            [{"value": "Some subject"}],
            ["custom_fields.imperial:domain_metadata.0.id"],
            400,
            id="missing-id",
        ),
        pytest.param(
            [{"id": "example-domain-term", "value": ""}],
            [{"id": "example-domain-term"}],
            ["custom_fields.imperial:domain_metadata.0.value"],
            400,
            id="blank-value",
        ),
        pytest.param(
            [{"id": "example-domain-term"}],
            [{"id": "example-domain-term"}],
            ["custom_fields.imperial:domain_metadata.0.value"],
            400,
            id="missing-value",
        ),
    ],
)
def test_domain_metadata_custom_field(
    user_client,
    location,
    vocabularies,
    user_depositor,
    api_headers,
    metadata,
    entries,
    expected_stored,
    expected_errors,
    publish_status,
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
    entry on an otherwise-201 response, rather than a hard rejection on
    create. Strict validation only happens at publish time - checked here
    for the invalid cases only (`publish_status` is None for valid-pairs,
    since actually succeeding at publish also requires a community
    submission unrelated to domain_metadata; the draft-level checks above
    already prove domain_metadata itself raises no error for valid input).
    """
    _grant_domain_metadata_permission(user_depositor, db)
    record_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {"imperial:domain_metadata": entries},
    }
    record = user_client.post(
        "/records",
        json=record_json,
        headers=api_headers,
    )
    assert record.status_code == 201

    error_fields = [e["field"] for e in record.json.get("errors", [])]
    assert sorted(error_fields) == sorted(expected_errors)

    stored_entries = record.json["custom_fields"].get("imperial:domain_metadata", [])
    assert stored_entries == expected_stored

    if publish_status is not None:
        publish = user_client.post(
            f"/records/{record.json['id']}/draft/actions/publish",
            headers=api_headers,
        )
        assert publish.status_code == publish_status


def test_domain_metadata_custom_field_search(
    user_client, location, vocabularies, user_depositor, api_headers, metadata, db
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
    other_metadata = {**metadata, "title": "Unrelated other record"}
    without_domain_metadata = {
        "metadata": other_metadata,
        "files": {"enabled": False},
    }

    matching_record = user_client.post(
        "/records", json=with_domain_metadata, headers=api_headers
    )
    assert matching_record.status_code == 201
    other_record = user_client.post(
        "/records", json=without_domain_metadata, headers=api_headers
    )
    assert other_record.status_code == 201

    current_search.flush_and_refresh("*")

    # matches on the entry's "value" (a word unique to this test) and finds
    # only this record, since nothing else in the suite uses it ...
    for q in ("quokka", "unicorn"):
        result = user_client.get(f"/user/records?q={q}", headers=api_headers)
        assert result.status_code == 200
        hit_ids = [hit["id"] for hit in result.json["hits"]["hits"]]
        assert hit_ids == [matching_record.json["id"]]

    # ... and on the entry's "id" -- other tests' records may share this
    # vocabulary id, so only assert this record is among the matches (and
    # that the record with no domain metadata at all is not).
    result = user_client.get("/user/records?q=example-domain-term", headers=api_headers)
    assert result.status_code == 200
    hit_ids = {hit["id"] for hit in result.json["hits"]["hits"]}
    assert matching_record.json["id"] in hit_ids
    assert other_record.json["id"] not in hit_ids

    # a term present in neither record matches nothing.
    result = user_client.get("/user/records?q=qwertyxyz999", headers=api_headers)
    assert result.status_code == 200
    assert result.json["hits"]["hits"] == []

    # sanity check: both records are otherwise listed (proves the filtering
    # above is the query doing its job, not the other record being hidden).
    result = user_client.get("/user/records", headers=api_headers)
    assert result.status_code == 200
    all_ids = {hit["id"] for hit in result.json["hits"]["hits"]}
    assert {matching_record.json["id"], other_record.json["id"]} <= all_ids


def test_domain_metadata_landing_page_shows_resolved_vocabulary(
    user_client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: landing-page (UI) display resolves terms."""
    _grant_domain_metadata_permission(user_depositor, db)
    record_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [
                {"id": "example-domain-term", "value": "Full props term"},
                {"id": "minimal-domain-term", "value": "Minimal term"},
            ]
        },
    }
    record = user_client.post("/records", json=record_json, headers=api_headers)
    assert record.status_code == 201, record.json

    ui_headers = {**api_headers, "Accept": "application/vnd.inveniordm.v1+json"}
    result = user_client.get(f"/records/{record.json['id']}/draft", headers=ui_headers)
    assert result.status_code == 200

    entries = result.json["ui"]["custom_fields"]["imperial:domain_metadata"]
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
    user_client, location, vocabularies, user_depositor, api_headers, metadata
):
    """imperial:domain_metadata: absent from the landing-page UI when unset."""
    record = user_client.post(
        "/records",
        json={"metadata": metadata, "files": {"enabled": False}},
        headers=api_headers,
    )
    assert record.status_code == 201, record.json

    ui_headers = {**api_headers, "Accept": "application/vnd.inveniordm.v1+json"}
    result = user_client.get(f"/records/{record.json['id']}/draft", headers=ui_headers)
    assert result.status_code == 200

    assert "imperial:domain_metadata" not in result.json["ui"]["custom_fields"]


@pytest.mark.parametrize("grant", [True, False])
def test_domain_metadata_create_requires_permission(
    grant, client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: create is gated by the permission."""
    if grant:
        _grant_domain_metadata_permission(user_depositor, db)

    record_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "v1"}]
        },
    }
    result = client.post("/records", json=record_json, headers=api_headers)
    assert result.status_code == (201 if grant else 403)
    if grant:
        assert result.json["custom_fields"]["imperial:domain_metadata"] == [
            {"id": "example-domain-term", "value": "v1"}
        ]


@pytest.mark.parametrize("grant", [True, False])
def test_domain_metadata_add_requires_permission(
    grant, client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: adding it later is gated by the permission."""
    plain = client.post(
        "/records",
        json={"metadata": metadata, "files": {"enabled": False}},
        headers=api_headers,
    )
    assert plain.status_code == 201
    rec_id = plain.json["id"]

    if grant:
        _grant_domain_metadata_permission(user_depositor, db)

    update_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "v1"}]
        },
    }
    result = client.put(
        f"/records/{rec_id}/draft",
        json=update_json,
        headers=_csrf_headers(client, api_headers),
    )
    assert result.status_code == (200 if grant else 403)
    if grant:
        assert result.json["custom_fields"]["imperial:domain_metadata"] == [
            {"id": "example-domain-term", "value": "v1"}
        ]


@pytest.mark.parametrize("grant", [True, False])
def test_domain_metadata_reorder_requires_permission(
    grant, client, location, vocabularies, user_depositor, api_headers, metadata, db
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
    created = client.post("/records", json=original_json, headers=api_headers)
    assert created.status_code == 201
    rec_id = created.json["id"]
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
    result = client.put(
        f"/records/{rec_id}/draft",
        json=reordered_json,
        headers=_csrf_headers(client, api_headers),
    )
    assert result.status_code == (200 if grant else 403)
    if grant:
        assert result.json["custom_fields"]["imperial:domain_metadata"] == [
            {"id": "minimal-domain-term", "value": "B"},
            {"id": "example-domain-term", "value": "A"},
        ]


@pytest.mark.parametrize("grant", [True, False])
def test_domain_metadata_removal_requires_permission(
    grant, client, location, vocabularies, user_depositor, api_headers, metadata, db
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
    created = client.post("/records", json=original_json, headers=api_headers)
    assert created.status_code == 201
    rec_id = created.json["id"]
    if not grant:
        _revoke_domain_metadata_permission(user_depositor, db)

    removal_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {"imperial:domain_metadata": []},
    }
    result = client.put(
        f"/records/{rec_id}/draft",
        json=removal_json,
        headers=_csrf_headers(client, api_headers),
    )
    assert result.status_code == (200 if grant else 403)
    if grant:
        assert result.json["custom_fields"].get("imperial:domain_metadata", []) == []


@pytest.mark.parametrize("grant", [True, False])
def test_domain_metadata_unchanged_update_requires_permission(
    grant, client, location, vocabularies, user_depositor, api_headers, metadata, db
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
    created = client.post("/records", json=original_json, headers=api_headers)
    assert created.status_code == 201
    rec_id = created.json["id"]
    if not grant:
        _revoke_domain_metadata_permission(user_depositor, db)

    unchanged_metadata = {
        **metadata,
        "title": "Updated title, domain metadata untouched",
    }
    unchanged_json = {
        "metadata": unchanged_metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "A"}]
        },
    }
    result = client.put(
        f"/records/{rec_id}/draft",
        json=unchanged_json,
        headers=_csrf_headers(client, api_headers),
    )
    assert result.status_code == (200 if grant else 403)
