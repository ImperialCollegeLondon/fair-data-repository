"""Site Metadata service."""

from invenio_records_resources.services import Service
from invenio_records_resources.services.uow import RecordCommitOp, unit_of_work

from .errors import MetadataValidationError, UnsupportedFormatError
from .schema import build_validators


class SiteMetadataService(Service):
    """Upload + validate per-format metadata file for a draft record."""

    def __init__(self, config):
        """Constructor."""
        super().__init__(config)
        self._validators = build_validators(config.supported_formats)

    def _require(self, action, identity, **kwargs):
        """Require permission for action."""
        self.require_permission(action, identity, **kwargs)

    def index(self, identity, record):
        """Index metadata files for a published record.

        This method is called by the RDMMetadataIndexComponent
        when a record is published.

        Args:
            identity: The identity performing the action
            record: The published record with metadata files
        """
        # Call the index method on all components
        for component in self.components:
            if hasattr(component, "index"):
                component.index(identity, record=record)

    @unit_of_work()
    def upload_and_validate(
        self, identity, record_id, fmt, file_stream, filename, uow=None
    ):
        """Upload and validate metadata file for a draft record."""
        self._require("upload_validate", identity, record_id=record_id, format=fmt)

        if fmt not in self._validators:
            raise UnsupportedFormatError(fmt)

        records_service = self.config.records_service
        draft_item = records_service.read_draft(identity, record_id)
        draft = draft_item._record

        file_key = f"metadata-{fmt}{self._infer_ext(filename)}"
        files = draft.files
        if file_key in files:
            obj = files.get(file_key).object_version
        else:
            obj = files.create(file_key).object_version

        # Store file content
        with obj.file.storage().open("wb") as fp:
            chunk = file_stream.read()
            fp.write(chunk)

        # Validate
        try:
            self._validators[fmt](chunk)
        except ValueError as ve:
            raise MetadataValidationError(fmt, [str(ve)])

        attr = self.config.site_metadata_attr
        draft.setdefault(attr, {})
        draft[attr][fmt] = {"file_key": file_key, "validated": True}

        uow.register(RecordCommitOp(draft, indexer=self.indexer))

        return self.result_item(
            self,
            identity,
            None,
            record_id=record_id,
            fmt=fmt,
            file_key=file_key,
            valid=True,
            errors=[],
        )

    @staticmethod
    def _infer_ext(filename):
        """Infer file extension from filename."""
        if "." in filename:
            return "." + filename.rsplit(".", 1)[1]
        return ""
