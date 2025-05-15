"""Determine file paths for records in Invenio RDM."""

from invenio_app.factory import create_app
from invenio_rdm_records.records import RDMRecord

app = create_app()

with app.app_context():
    record = RDMRecord.pid.resolve("8cqnb-ek771")
    for file_obj in record.files.values():
        obj = file_obj.object_version
        file_storage = obj.file.storage()
        if obj:
            print("Key:", obj.key)
            print("Path:", obj.file.uri)
            print("File Storage:", file_storage)
            print()
