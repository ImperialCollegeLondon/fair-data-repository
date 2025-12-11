"""Module for custom service components."""

from flask import current_app
from invenio_records_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import TaskOp

from .tasks import export_record_to_symplectic


class SymplecticComponent(ServiceComponent):
    """Service component handling synchronisation to Symplectic."""

    def publish(self, identity, draft=None, record=None):
        """Enqueue celery task to publish a record to Symplectic."""
        if record:
            self.uow.register(TaskOp(export_record_to_symplectic, record))


class RDMMetadataIndexComponent(ServiceComponent):
    """Component for RDMRecordService: triggers metadata indexing on publish.

    This component is attached to the RDMRecordService and calls the
    SiteMetadataService to perform the actual indexing.
    """

    def publish(self, identity, draft=None, record=None):
        """Trigger metadata indexing when a record is published."""
        if not record:
            return

        # Get the site-metadata service from the app extensions
        site_metadata_ext = current_app.extensions.get("site-metadata")
        if not site_metadata_ext:
            return

        # Call the index method on the SiteMetadataService
        site_metadata_ext.service.index(identity, record)
