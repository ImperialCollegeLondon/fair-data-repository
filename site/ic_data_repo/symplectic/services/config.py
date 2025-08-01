"""Imperial College Data Repository Symplectic Service Configuration."""

from invenio_records_resources.services import ServiceConfig
from invenio_records_resources.services.base.config import ConfiguratorMixin

from .permissions import SymplecticPermissionPolicy
from .result_items import SymplecticRelatedObjectsResult


class SymplecticServiceConfig(ServiceConfig, ConfiguratorMixin):
    """Configuration for the Symplectic service."""

    permission_policy_cls = SymplecticPermissionPolicy
    result_item_cls = SymplecticRelatedObjectsResult

    @classmethod
    def build(cls, app):
        """Build the service configuration."""
        config = super().build(app)
        # Additional configuration can be set here if needed
        config.symplectic_api_url = app.config.get("SYMPLECTIC_API_URL", "")
        config.symplectic_api_key = app.config.get("SYMPLECTIC_API_KEY", "")
        return config
