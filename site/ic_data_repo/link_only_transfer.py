"""Link-only file transfer implementation."""

from flask import current_app
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_records_resources.services.files.schema import BaseTransferSchema
from invenio_records_resources.services.files.transfer import Transfer, TransferStatus
from marshmallow import fields

LINK_ONLY_TRANSFER_TYPE = "X"
"""Link-only transfer type identifier."""


class LinkOnlyTransferSchema(BaseTransferSchema):
    """Schema for link-only transfer type."""

    url = fields.Url(required=True, load_only=True)
    """URL that points to the remote file.

    The file may be accessed by using the /content url and then a 302 redirect
    is sent to the client with the actual URI.
    """


class LinkOnlyTransfer(Transfer):
    """Metadata-only file transfer type pointing to an external URL."""

    transfer_type = LINK_ONLY_TRANSFER_TYPE

    Schema = LinkOnlyTransferSchema

    @property
    def status(self):
        """Get the status of the transfer."""
        # always return completed for remote files
        return TransferStatus.COMPLETED

    def send_file(self, *, as_attachment, **kwargs):
        """Send the file to the client."""
        return current_app.response_class(
            status=302,
            headers={
                "Location": self.file_record.transfer["url"],
            },
        )

    def init_file(self, record, file_metadata, **kwargs):
        """Initialize a file and return a file record."""
        url = file_metadata["transfer"]["url"]
        # all remote file records with the same URL share the same FileInstance
        fi = FileInstance.get_by_uri(url)
        if fi is None:
            fi = FileInstance.create()
            fi.set_uri(
                uri=file_metadata.get("transfer", {}).get("url"),
                size=file_metadata.get("size"),
                checksum=file_metadata.get("checksum"),
                readable=False,
            )
        obj = ObjectVersion.create(record.files.bucket, file_metadata["key"], fi.id)
        return super().init_file(record, file_metadata, obj=obj)
