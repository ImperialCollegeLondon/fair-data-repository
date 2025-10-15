"""Link-only file transfer implementation."""

from invenio_records_resources.services.files.schema import BaseTransferSchema
from invenio_records_resources.services.files.transfer import Transfer
from marshmallow import ValidationError, fields, validates

LINK_ONLY_TRANSFER_TYPE = "X"
"""Link-only transfer type identifier."""


class LinkOnlyTransfer(Transfer):
    """Metadata-only file transfer type pointing to an external URL."""

    transfer_type = LINK_ONLY_TRANSFER_TYPE

    class Schema(BaseTransferSchema):
        """Schema for link-only transfer type."""

        url = fields.Url(required=True)  # where the bits live
        size = fields.Int(load_default=None)  # optional, for UI
        checksum = fields.String(load_default=None)  # optional, for UI
        # optionally: mime, filename_hint, etc.

        @validates("size")
        def _size_nonneg(self, v, **_):
            if v is not None and v < 0:
                raise ValidationError("size must be >= 0")

    def create(self, *, identity, uow, data, **kwargs):
        """Register file entry and persist link metadata."""
        f = self.file_service.file_manager.create_file_record(self.record, self.key)

        # attach transfer marker + your public metadata
        f.transfer = {"type": self.transfer_type}

        # stash the target URL somewhere retrievable by read_content()
        # Two common options:
        #  a) put it in f.metadata (exposed in API)
        #  b) use a custom model column/rel (hidden)
        f.metadata = (f.metadata or {}) | {
            "url": data["url"],
            "size": data.get("size"),
            "checksum": data.get("checksum"),
        }
        uow.register(f.model)  # schedule DB write

        return f

    def read_content(self, *, identity, range=None, **kwargs):
        """Defines how GET .../content should behave."""
        f = self.file_service.file_manager.get_file_record(self.record, self.key)
        url = (f.metadata or {}).get("url")

        if not url:
            # normalise to a 404/410 response
            return {"status_code": 404}

        # EITHER: simple redirect
        return {"redirect": url}

        # OR: stream/proxy yourself and return a Werkzeug Response
        # return self._proxy_stream(url, range=range)
