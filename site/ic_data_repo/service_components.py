"""Module for custom service components."""

from flask_principal import Identity
from invenio_records_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import TaskOp
from invenio_vocabularies.proxies import current_service as vocabularies_service

from .tasks import export_record_to_symplectic


class SymplecticComponent(ServiceComponent):
    """Service component handling synchronisation to Symplectic."""

    def publish(self, identity, draft=None, record=None):
        """Enqueue celery task to publish a record to Symplectic."""
        if record:
            self.uow.register(TaskOp(export_record_to_symplectic, record))


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
