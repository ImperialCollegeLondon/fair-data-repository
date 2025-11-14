"""Module for custom service components."""

from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import TaskOp

from .tasks import export_record_to_symplectic


class SymplecticComponent(ServiceComponent):
    """Service component handling synchronisation to Symplectic."""

    def publish(self, identity, draft=None, record=None):
        """Enqueue celery task to publish a record to Symplectic."""
        if record:
            self.uow.register(TaskOp(export_record_to_symplectic, record))


class ForceCommunityComponent(ServiceComponent):
    """Service component to add records to the Imperial community."""

    def create(self, identity, record=None, **kwargs):
        """Open Imperial community review request on record creation."""
        if record is None:
            return

        community = current_communities.service.read(identity, "icl")
        request = {
            "type": "community-submission",
            "receiver": {"community": community.data["id"]},
        }

        # This is enough to make the UI use the review mechanism.
        current_rdm_records_service.review.create(identity, data=request, record=record)
