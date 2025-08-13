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

    def fetch_related_objects(self, identity, search_query, search_type):
        """Fetch related objects for a given DOI."""
        # Check permissions
        self.require_permission(identity, "read")

        try:
            # Call the search_symplectic method instead of fetch_related_objects
            search_results = self._client.search_symplectic(search_query, search_type)
            # Return wrapped result
            return self.config.result_item_cls(self, identity, search_results)
        except Exception as e:
            raise SymplecticServiceError(
                f"Failed to fetch related objects: {str(e)}"
            ) from e
