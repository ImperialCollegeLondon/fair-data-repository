"""Imperial College Data Repository Symplectic Service Module."""

from invenio_records_resources.services import Service

from ...symplectic_interface import SymplecticClient
from .errors import SymplecticServiceError


class SymplecticService(Service):
    """Service for Symplectic API interactions."""

    def __init__(self, config):
        """Initialize the Symplectic service with configuration."""
        super().__init__(config)
        # Initialize the Symplectic client from config
        self._client = SymplecticClient(
            api_url=config.symplectic_api_url, api_key=config.symplectic_api_key
        )

    def fetch_related_objects(self, identity, doi):
        """Fetch related objects for a given DOI."""
        # Check permissions

        self.require_permission(identity, "read")

        try:
            # Call the symplectic interface
            related_object_ids = self._client.fetch_related_objects(doi)
            # Return wrapped result
            return self.config.result_item_cls(self, identity, related_object_ids)
        except Exception as e:
            raise SymplecticServiceError(f"Failed to fetch related objects") from e
