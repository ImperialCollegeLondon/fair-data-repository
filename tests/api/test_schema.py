"""Tests for the metadata schema."""

from datetime import date

from invenio_rdm_records.proxies import current_rdm_records_service


def test_metadata_schema(vocabularies, user_depositor, metadata):
    """Test that the metadata schema is enforced."""
    metadata["publisher"] = "Fake Publisher"
    metadata["publication_date"] = "1970-01-01"
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record["status"] == "draft_with_review"

    # Test metadata policies are enforced.
    assert record["metadata"]["title"] == "Test Record"
    assert record["metadata"]["creators"][0]["person_or_org"]["given_name"] == "Neo"
    assert "role" not in record["metadata"]["creators"][0]
    assert record["metadata"]["publisher"] == "Imperial College London"
    assert record["metadata"]["publication_date"] == date.today().isoformat()


def test_metadata_schema_rights(vocabularies, user_depositor, metadata):
    """Test that the rights schema is enforced."""
    # Test that no license is accepted.
    metadata["rights"] = []
    record_1 = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record_1["status"] == "draft_with_review"
    assert "rights" not in record_1["metadata"]

    # Test that a single license is accepted.
    metadata["rights"] = [{"id": "cc0-1.0"}]
    record_2 = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record_2["status"] == "draft_with_review"
    assert record_2["metadata"]["rights"][0]["id"] == "cc0-1.0"

    # Test that multiple rights entries are not accepted.
    metadata["rights"] = [{"id": "cc0-1.0"}, {"id": "cc-by-4.0"}]
    record_3 = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record_3["status"] == "draft_with_review"
    error = record_3.errors[0]
    assert error["field"] == "metadata.rights"
    assert error["messages"] == ["No more than one can be provided."]
    assert "rights" not in record_3["metadata"]


def test_metadata_schema_copyright(vocabularies, user_depositor, metadata):
    """Test that the copyright metadata field is blocked."""
    metadata["copyright"] = "some data"
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata},
    )
    assert record["status"] == "draft_with_review"
    error = record.errors[0]
    assert error["field"] == "metadata.copyright"
    assert error["messages"] == ["Unknown field."]
    assert "copyright" not in record["metadata"]


def test_access_schema(vocabularies, user_depositor, metadata):
    """Test that the access schema is enforced."""
    access = {"record": "restricted", "files": "restricted"}
    record = current_rdm_records_service.create(
        user_depositor.identity,
        data={"metadata": metadata, "access": access},
    )
    assert record["status"] == "draft_with_review"
    # 'record' should be reset to public, but 'files' should remain restricted.
    assert record["access"]["record"] == "public"
    assert record["access"]["files"] == "restricted"
