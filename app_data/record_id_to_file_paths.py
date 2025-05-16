"""Determine file paths for records in Invenio RDM."""

import argparse

from invenio_app.factory import create_app
from invenio_rdm_records.records import RDMRecord


def get_file_paths(record_id: str) -> None:
    """Get file paths for a given record ID.

    Args:
        record_id: The ID of the record to retrieve.
    """
    record = RDMRecord.pid.resolve(record_id)
    for file_obj in record.files.values():
        if obj := file_obj.object_version:
            print("Key:", obj.key)
            print("Path:", obj.file.uri)
            print("Storage:", obj.file.storage())
            print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get file paths for records.")
    parser.add_argument("record_id", help="The ID of the record to retrieve.")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        get_file_paths(args.record_id)
