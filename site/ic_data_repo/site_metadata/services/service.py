"""Site Metadata service."""

from io import BytesIO

from invenio_records_resources.services import Service
from invenio_records_resources.services.uow import unit_of_work

from .errors import UnsupportedFormatError
from .schema import build_validators


class SiteMetadataService(Service):
    """Upload + validate per-format metadata file for a draft record."""

    def __init__(self, config):
        """Constructor."""
        super().__init__(config)
        self._validators = build_validators(config.supported_formats)

    def _require(self, action, identity, **kwargs):
        """Require permission for action."""
        self.require_permission(identity, action, **kwargs)

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
    def upload_and_validate(self, identity, record_id, fmt, file, uow=None):
        """Upload and validate metadata file for a draft record."""
        self._require("upload_validate", identity, record_id=record_id, format=fmt)

        if fmt not in self._validators:
            raise UnsupportedFormatError(fmt)

        records_service = self.config.records_service
        file_contents = file.stream.read()

        key = file.filename
        draft_file_service = records_service.draft_files
        draft_file_service.init_files(identity, record_id, [dict(key=key)])
        draft_file_service.set_file_content(
            identity, record_id, key, BytesIO(file_contents)
        )
        draft_file_service.commit_file(identity, record_id, key)

        try:
            self._validators[fmt](file_contents)
        except ValueError as e:
            return self.result_item(
                identity,
                record_id=record_id,
                fmt=fmt,
                file_key=key,
                valid=False,
                errors=[str(e)],
            )

        return self.result_item(
            identity,
            record_id=record_id,
            fmt=fmt,
            file_key=key,
            valid=True,
            errors=[],
        )

    @staticmethod
    def _infer_ext(filename):
        """Infer file extension from filename."""
        if "." in filename:
            return "." + filename.rsplit(".", 1)[1]
        return ""
