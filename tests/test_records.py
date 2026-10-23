"""Tests for records."""

from invenio_access.permissions import system_identity


def test_new_record_version(record_tester):
    """Test creating a new version of a record."""
    record_test = record_tester()
    record_test.create()
    record_test.publish(identity=system_identity)

    # Create version 2 of the record.
    record_test.new_version()
    record_test.publish(identity=system_identity)
