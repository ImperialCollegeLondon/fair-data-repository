"""Module for custom service components."""

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

    def _enforce_restricted_license_permission(self, identity, data):
        """Check if a restricted license is requested and test permission."""
        deposit_licenses = data and data.get("metadata", {}).get("rights", [])
        restricted_licenses = vocabularies_service.search(
            identity, type="licenses", params=dict(tags=["restricted"])
        )
        restricted_license_ids = {dl["id"] for dl in restricted_licenses.hits}

        if any(dl["id"] in restricted_license_ids for dl in deposit_licenses):
            self.service.require_permission(identity, "select_restricted_license")

    def create(self, identity, data=None, record=None, **kwargs):
        """Check if user has permission to create a record with a restricted license."""
        self._enforce_restricted_license_permission(identity, data)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        """Check if user has permission to update a draft with a restricted license."""
        self._enforce_restricted_license_permission(identity, data)
