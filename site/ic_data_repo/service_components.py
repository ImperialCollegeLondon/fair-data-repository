"""Module for custom service components."""

from invenio_access import Permission
from invenio_access.permissions import system_process
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_records_resources.services.files.components import FileServiceComponent
from invenio_records_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import TaskOp

from .description_transfer import DESCRIPTION_TRANSFER_TYPE
from .permissions import described_file_action
from .tasks import export_record_to_symplectic


class SymplecticComponent(ServiceComponent):
    """Service component handling synchronisation to Symplectic."""

    def publish(self, identity, draft=None, record=None):
        """Enqueue celery task to publish a record to Symplectic."""
        if record:
            self.uow.register(TaskOp(export_record_to_symplectic, record))


class DescribedFilePermissionComponent(FileServiceComponent):
    """Restrict mutating operations on described files."""

    @staticmethod
    def _require_permission(identity):
        if system_process in identity.provides:
            return

        if not Permission(described_file_action).allows(identity):
            raise PermissionDeniedError()

    def init_files(self, identity, id_, record, data):
        """Init files handler."""
        for file_metadata in data:
            transfer_type = file_metadata.get("transfer", {}).get("type")
            if transfer_type == DESCRIPTION_TRANSFER_TYPE:
                self._require_permission(identity)

    def set_file_content(self, identity, id_, file_key, stream, content_length, record):
        """Set file content handler."""
        transfer_type = record.files[file_key].transfer.transfer_type
        if transfer_type == DESCRIPTION_TRANSFER_TYPE:
            self._require_permission(identity)

    def commit_file(self, identity, id_, file_key, record):
        """Commit file handler."""
        transfer_type = record.files[file_key].transfer.transfer_type
        if transfer_type == DESCRIPTION_TRANSFER_TYPE:
            self._require_permission(identity)
