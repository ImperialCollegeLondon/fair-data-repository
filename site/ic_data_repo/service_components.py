"""Module for custom service components."""

from invenio_records_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import TaskOp

from .tasks import export_record_to_symplectic


class SymplecticComponent(ServiceComponent):
    """Service component handling synchronisation to Symplectic."""

    def publish(self, identity, draft=None, record=None):
        """Enqueue celery task to publish a record to Symplectic."""
        if record:
            self.uow.register(TaskOp(export_record_to_symplectic, record))


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
