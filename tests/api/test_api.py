"""Tests for the API."""

from datetime import date

import pytest
from ic_data_repo.config.custom_fields import RDM_CUSTOM_FIELDS_UI
from ic_data_repo.permissions import domain_metadata_action
from invenio_access.permissions import ActionUsers
from invenio_search.proxies import current_search


@pytest.fixture
def metadata():
    """Simple record metadata."""
    return {
        "title": "Test Record",
        "description": "This is a test record.",
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "given_name": "Neo",
                    "family_name": "Anderson",
                },
                "role": "the one",
            },
        ],
    }


@pytest.fixture
def access():
    """Simple access schema."""
    return {
        "record": "public",
        "files": "public",
    }


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


def test_metadata_schema(
    client, location, vocabularies, user_depositor, api_headers, metadata, access
):
    """Test that the metadata schema is enforced."""
    metadata["resource_type"] = "fake_resource_type"
    metadata["publisher"] = "Fake Publisher"
    metadata["publication_date"] = "1970-01-01"
    access["record"] = "restricted"
    access["files"] = "restricted"
    result = client.post(
        "/records",
        json={"metadata": metadata, "access": access},
        headers=api_headers,
    )
    assert result.status_code == 201

    # Test metadata policies are enforced.
    assert result.json["metadata"]["title"] == "Test Record"
    assert result.json["metadata"]["resource_type"]["id"] == "dataset"
    assert (
        result.json["metadata"]["creators"][0]["person_or_org"]["given_name"] == "Neo"
    )
    assert "role" not in result.json["metadata"]["creators"][0]
    assert result.json["metadata"]["publisher"] == "Imperial College London"
    assert result.json["metadata"]["publication_date"] == date.today().isoformat()

    # Test access policies are enforced.
    # 'record' should be reset to public, but 'files' should remain restricted.
    assert result.json["access"]["record"] == "public"
    assert result.json["access"]["files"] == "restricted"


def test_metadata_schema_rights(
    client, location, vocabularies, user_depositor, api_headers, metadata
):
    """Test that the rights schema is enforced."""
    # Test that no license is accepted.
    metadata["rights"] = []
    result = client.post(
        "/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert "rights" not in result.json["metadata"]

    # Test that a single license is accepted.
    metadata["rights"] = [{"id": "cc0-1.0"}]
    result = client.post(
        "/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert result.json["metadata"]["rights"][0]["id"] == "cc0-1.0"

    # Test that multiple rights entries are not accepted.
    metadata["rights"] = [{"id": "cc0-1.0"}, {"id": "cc-by-4.0"}]
    result = client.post(
        "/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    assert result.json["errors"][0]["messages"][0].startswith("No more than")


def test_metadata_schema_copyright(
    client, location, vocabularies, user_depositor, api_headers, metadata
):
    """Test that the copyright metadata field is blocked."""
    metadata["copyright"] = "some data"
    result = client.post(
        "/records",
        json={"metadata": metadata},
        headers=api_headers,
    )
    assert result.status_code == 201
    error = result.json["errors"][0]
    assert error["field"] == "metadata.copyright"
    assert error["messages"] == ["Unknown field."]
    assert "copyright" not in result.json["metadata"]


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


def test_new_record_version(
    user_client, location, vocabularies, user_depositor, api_headers, metadata
):
    """Test creating a new version of a record."""
    record_v1_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {"imperial:dart_id": "123456789"},
    }
    record_v1 = user_client.post(
        "/records",
        json=record_v1_json,
        headers=api_headers,
    )
    assert record_v1.status_code == 201
    record_v1_id = record_v1.json["id"]

    community_json = {
        "slug": "icl",
        "metadata": {"title": "Imperial College London"},
        "access": {"visibility": "public"},
    }
    community = user_client.post(
        "/communities",
        json=community_json,
        headers=api_headers,
    )
    assert community.status_code == 201
    community_id = community.json["id"]

    community_submit_json = {
        "receiver": {"community": community_id},
        "type": "community-submission",
    }
    community_submit = user_client.put(
        f"/records/{record_v1_id}/draft/review",
        json=community_submit_json,
        headers=api_headers,
    )
    assert community_submit.status_code == 200
    community_submit_id = community_submit.json["id"]

    comunity_review = user_client.post(
        f"/records/{record_v1_id}/draft/actions/submit-review",
        headers=api_headers,
    )
    assert comunity_review.status_code == 202

    accept_submission = user_client.post(
        f"/requests/{community_submit_id}/actions/accept", headers=api_headers
    )
    assert accept_submission.status_code == 200
    assert accept_submission.json["status"] == "accepted"

    record_v2 = user_client.post(
        f"/records/{record_v1_id}/versions",
        headers=api_headers,
    )
    assert record_v2.status_code == 201
    record_v2_id = record_v2.json["id"]

    record_v2_published = user_client.post(
        f"/records/{record_v2_id}/draft/actions/publish",
        headers=api_headers,
    )
    assert record_v2_published.status_code == 202


def test_domain_metadata_landing_page_shows_resolved_vocabulary(
    user_client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: landing-page (UI) display resolves terms.

    Resolves each entry's vocabulary term, adding a title and (safe,
    http(s)-only) DataCite-style scheme/value URIs alongside the stored
    id/value - see DomainMetadataCF.ui_field / DomainMetadataItemUISchema
    and the domain_metadata.html landing-page template that consumes this.

    Covers a term with full props (example-domain-term) and one with no
    props at all (minimal-domain-term), confirming the latter degrades to
    just a title with null props rather than erroring.
    """
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
    """imperial:domain_metadata: absent from the landing-page UI when unset.

    The landing-page macro's `{% if field_value %}` check sees a falsy
    (missing/empty) value and skips the section entirely - so it isn't
    dumped into the UI payload at all.
    """
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


def test_domain_metadata_hidden_from_upload_form():
    """imperial:domain_metadata must never be editable on the upload form.

    It's populated via bulk import, not by hand (see RDM_CUSTOM_FIELDS_UI
    in site/ic_data_repo/config/custom_fields.py). get_form_config()
    (invenio_app_rdm) drops any section with hide_from_upload_form=True
    before it reaches the deposit form's React config, so asserting the
    flag here is sufficient to guarantee that.
    """
    domain_metadata_sections = [
        section
        for section in RDM_CUSTOM_FIELDS_UI
        if any(f["field"] == "imperial:domain_metadata" for f in section["fields"])
    ]
    assert len(domain_metadata_sections) == 1
    assert domain_metadata_sections[0]["hide_from_upload_form"] is True


def test_domain_metadata_create_requires_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata
):
    """imperial:domain_metadata: create is denied without the permission.

    Creating a record with imperial:domain_metadata already populated is
    denied without the domain-metadata-action permission (still needs
    deposit-action too, granted by the user_depositor fixture as normal).
    """
    record_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "v1"}]
        },
    }
    result = client.post("/records", json=record_json, headers=api_headers)
    assert result.status_code == 403


def test_domain_metadata_create_allowed_with_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: create succeeds once permission is granted.

    With domain-metadata-action granted, creating a record with
    imperial:domain_metadata populated succeeds and persists it.
    """
    _grant_domain_metadata_permission(user_depositor, db)

    record_json = {
        "metadata": metadata,
        "files": {"enabled": False},
        "custom_fields": {
            "imperial:domain_metadata": [{"id": "example-domain-term", "value": "v1"}]
        },
    }
    result = client.post("/records", json=record_json, headers=api_headers)
    assert result.status_code == 201
    assert result.json["custom_fields"]["imperial:domain_metadata"] == [
        {"id": "example-domain-term", "value": "v1"}
    ]


def test_domain_metadata_add_requires_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata
):
    """imperial:domain_metadata: adding it later is denied without permission.

    Adding imperial:domain_metadata to a record that didn't have any is
    denied without the permission - the create itself needs no special
    permission here, since it doesn't touch the field at all.
    """
    plain = client.post(
        "/records",
        json={"metadata": metadata, "files": {"enabled": False}},
        headers=api_headers,
    )
    assert plain.status_code == 201
    rec_id = plain.json["id"]

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
    assert result.status_code == 403


def test_domain_metadata_add_allowed_with_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: adding it later succeeds with permission.

    With the permission granted, adding imperial:domain_metadata to a
    record that didn't have any succeeds and persists it.
    """
    _grant_domain_metadata_permission(user_depositor, db)

    plain = client.post(
        "/records",
        json={"metadata": metadata, "files": {"enabled": False}},
        headers=api_headers,
    )
    assert plain.status_code == 201
    rec_id = plain.json["id"]

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
    assert result.status_code == 200
    assert result.json["custom_fields"]["imperial:domain_metadata"] == [
        {"id": "example-domain-term", "value": "v1"}
    ]


def test_domain_metadata_reorder_requires_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: reordering entries is denied without permission.

    Reordering existing imperial:domain_metadata entries is denied
    without the permission, even though the set of entries is unchanged.
    """
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
    assert result.status_code == 403


def test_domain_metadata_reorder_allowed_with_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: reordering succeeds with permission.

    With the permission granted, reordering existing entries succeeds and
    the new order is what's persisted.
    """
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
    assert result.status_code == 200
    assert result.json["custom_fields"]["imperial:domain_metadata"] == [
        {"id": "minimal-domain-term", "value": "B"},
        {"id": "example-domain-term", "value": "A"},
    ]


def test_domain_metadata_removal_requires_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: removing all entries is denied without permission.

    Removing all imperial:domain_metadata entries (submitting an empty
    list) is denied without the permission.
    """
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
    assert result.status_code == 403


def test_domain_metadata_removal_allowed_with_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """With the permission granted, removing all entries succeeds."""
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
    assert result.status_code == 200
    assert result.json["custom_fields"].get("imperial:domain_metadata", []) == []


def test_domain_metadata_unchanged_update_does_not_require_permission(
    client, location, vocabularies, user_depositor, api_headers, metadata, db
):
    """imperial:domain_metadata: an unchanged value doesn't require permission.

    Saving a draft with imperial:domain_metadata present but identical to
    what's already stored doesn't require the permission - the gate only
    fires on an actual diff (see DomainMetadataPermissionComponent).
    """
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
    assert result.status_code == 200
    assert (
        result.json["metadata"]["title"] == "Updated title, domain metadata untouched"
    )
    assert result.json["custom_fields"]["imperial:domain_metadata"] == [
        {"id": "example-domain-term", "value": "A"}
    ]
