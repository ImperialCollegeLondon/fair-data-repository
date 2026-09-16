"""Module for custom service components."""

from flask_principal import Identity
from invenio_access import Permission
from invenio_access.permissions import system_process
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_records_resources.services.files.components import FileServiceComponent
from invenio_records_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import TaskOp
from invenio_vocabularies.proxies import current_service as vocabularies_service

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


class RestrictedLicensePermissionComponent(ServiceComponent):
    """Service component to enforce restricted license permissions."""

    def _enforce_restricted_license_permission(
        self, identity: Identity, data: dict[str, object] | None
    ):
        """Check if a restricted license is requested and test permission."""
        if not data:
            return

        # As the schema of data is not guaranteed when this component runs, we need to
        # strictly check the types of the fields we access to avoid runtime errors. If
        # it's not what we expect, just skip the permission check and let a following
        # service component handle the validation and raise an error.
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            return
        deposit_licenses = metadata.get("rights")
        if not isinstance(deposit_licenses, list):
            return

        vocab_entries = vocabularies_service.read_many(
            identity, type="licenses", ids=[dl["id"] for dl in deposit_licenses]
        )

        if any("restricted" in entry["tags"] for entry in vocab_entries):
            self.service.require_permission(identity, "select_restricted_license")

    def create(self, identity, data=None, record=None, **kwargs):
        """Check if user has permission to create a record with a restricted license."""
        self._enforce_restricted_license_permission(identity, data)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        """Check if user has permission to update a draft with a restricted license."""
        self._enforce_restricted_license_permission(identity, data)


_MISSING = object()
"""Distinguishing "field not mentioned in this payload" from
"field explicitly present with an empty/falsy value" - imperial:domain_metadata
is hide_from_upload_form, so the deposit form's own payloads never mention it
at all, and that must not be misread as "the user is clearing it"."""


class DomainMetadataPermissionComponent(ServiceComponent):
    """Enforces the domain-metadata action permission.

    See ic_data_repo.permissions.domain_metadata_action - this sits on top
    of the normal record-access permissions the service already checks.

    Must run before CustomFieldsComponent (see RDM_RECORDS_SERVICE_COMPONENTS
    in config/settings.py) - that's what actually copies data["custom_fields"]
    onto the record, so this needs to run first to still see the *previous*
    value on `record` for comparison. Raising here (via require_permission)
    happens before any UnitOfWork operation for this request is registered,
    so a denial here means nothing about the request is persisted - not just
    this field, nothing at all - satisfying the "no partial mutation on
    authorization failure" requirement without needing an explicit rollback.
    """

    field = "imperial:domain_metadata"
    action_name = "edit_domain_metadata"

    def _value(self, obj):
        if not obj:
            return _MISSING
        return obj.get("custom_fields", {}).get(self.field, _MISSING)

    def _require_permission_if_changed(self, identity, data, record):
        new_value = self._value(data)
        if new_value is _MISSING:
            # this request's payload doesn't mention the field at all (e.g. a
            # depositor editing an unrelated field through the deposit form,
            # which never even sees this field) - nothing to gate.
            return

        old_value = self._value(record)
        if old_value is _MISSING:
            old_value = []

        if new_value != old_value:
            self.service.require_permission(identity, self.action_name)

    def create(self, identity, data=None, record=None, **kwargs):
        """Gate imperial:domain_metadata on the initial draft creation."""
        self._require_permission_if_changed(identity, data, record)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        """Gate any add/update/reorder/remove to imperial:domain_metadata."""
        self._require_permission_if_changed(identity, data, record)
