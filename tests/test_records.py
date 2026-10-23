"""Tests for records."""

from invenio_access.permissions import system_identity


def test_new_record_version(record_tester):
    """Test creating a new version of a record."""
    record = record_tester()
    record.create()
    record.publish(identity=system_identity)

    # Create version 2 of the record.
    record.new_version()
    record.publish(identity=system_identity)
