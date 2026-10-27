"""Tests for the metadata schema."""

from datetime import date


def test_metadata_schema(record_tester):
    """Test that the metadata schema is enforced."""
    record_tester.data["metadata"]["publisher"] = "Fake Publisher"
    record_tester.data["metadata"]["publication_date"] = "1970-01-01"
    record = record_tester.create()

    # Test metadata policies are enforced.
    assert record["metadata"]["title"] == "Test Record"
    assert record["metadata"]["creators"][0]["person_or_org"]["given_name"] == "Neo"
    assert "role" not in record["metadata"]["creators"][0]
    assert record["metadata"]["publisher"] == "Imperial College London"
    assert record["metadata"]["publication_date"] == date.today().isoformat()


def test_metadata_schema_rights(record_tester):
    """Test that the rights schema is enforced."""
    # Test that no license is accepted.
    record_tester.data["metadata"]["rights"] = []
    record_1 = record_tester.create()
    assert "rights" not in record_1["metadata"]

    # Test that a single license is accepted.
    record_tester.data["metadata"]["rights"] = [{"id": "cc0-1.0"}]
    record_2 = record_tester.create()
    assert record_2["metadata"]["rights"][0]["id"] == "cc0-1.0"

    # Test that multiple rights entries are not accepted.
    record_tester.data["metadata"]["rights"] = [{"id": "cc0-1.0"}, {"id": "cc-by-4.0"}]
    record_3 = record_tester.create()
    error = record_3.errors[0]
    assert error["field"] == "metadata.rights"
    assert error["messages"] == ["No more than one can be provided."]
    assert "rights" not in record_3["metadata"]


def test_metadata_schema_copyright(record_tester):
    """Test that the copyright metadata field is blocked."""
    record_tester.data["metadata"]["copyright"] = "some data"
    record = record_tester.create()
    error = record.errors[0]
    assert error["field"] == "metadata.copyright"
    assert error["messages"] == ["Unknown field."]
    assert "copyright" not in record["metadata"]


def test_access_schema(record_tester):
    """Test that the access schema is enforced."""
    record_tester.data["access"] = {"record": "restricted", "files": "restricted"}
    record = record_tester.create()
    # 'record' should be reset to public, but 'files' should remain restricted.
    assert record["access"]["record"] == "public"
    assert record["access"]["files"] == "restricted"
