"""Imperial College Data Repository Symplectic Service Configuration."""

from invenio_records_resources.services import ServiceConfig

from .permissions import SymplecticPermissionPolicy
from .result_items import SymplecticRelatedObjectsResult


class SymplecticServiceConfig(ServiceConfig):
    """Configuration for the Symplectic service."""

    permission_policy_cls = SymplecticPermissionPolicy

    result_item_cls = SymplecticRelatedObjectsResult

    @classmethod
    def build(cls, app):
        """Build the service configuration from the Flask app config."""
        config = cls()
        config.symplectic_api_url = app.config.get("SYMPLECTIC_API_URL", "")
        config.symplectic_api_key = app.config.get("SYMPLECTIC_API_KEY", "")
        return config
