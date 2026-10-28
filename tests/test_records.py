"""Tests for records."""

from invenio_access.permissions import system_identity


def test_new_record_version(record_tester):
    """Test creating a new version of a record."""
    record_tester.create()
    record_tester.publish(identity=system_identity)

    # Create version 2 of the record.
    record_tester.new_version()
    record_tester.publish(identity=system_identity)
