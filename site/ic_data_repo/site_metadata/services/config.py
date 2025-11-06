"""Site Metadata service configuration."""

from invenio_records_resources.services import ServiceConfig

from .permissions import SiteMetadataPermissionPolicy
from .result_items import MetadataValidationResult
from .schema import JSONMetadataSchema, MarshmallowValidator


class SiteMetadataServiceConfig(ServiceConfig):
    """Site Metadata service configuration."""

    permission_policy_cls = SiteMetadataPermissionPolicy
    result_item_cls = MetadataValidationResult

    # Inject the record (draft) service externally (e.g. rdm-records)
    _get_records_service = None

    @property
    def records_service(self):
        """Lazy-load records service."""
        if self._get_records_service:
            return self._get_records_service()
        return None

    site_metadata_attr = "site_metadata"

    supported_formats = {
        "json": {
            "validator": MarshmallowValidator(JSONMetadataSchema()),
            "index_name": "site-metadata-json",
        },
    }

    @classmethod
    def build(cls, app):
        """Build the service configuration from the Flask app config."""
        config = cls()
        config.site_metadata_attr = app.config.get(
            "IC_SITE_METADATA_ATTR", "site_metadata"
        )
        config.supported_formats = app.config.get(
            "IC_SITE_METADATA_FORMATS", config.supported_formats
        )
        return config
