"""Site Metadata service configuration."""

from invenio_records_resources.services import ServiceConfig

from .permissions import SiteMetadataPermissionPolicy
from .result_items import MetadataValidationResult
from .schema import JSONMetadataSchema, JSONSchemaValidator, MarshmallowValidator


class SiteMetadataServiceConfig(ServiceConfig):
    """Site Metadata service configuration."""

    permission_policy_cls = SiteMetadataPermissionPolicy
    result_item_cls = MetadataValidationResult

    # Inject the record (draft) service externally (e.g. rdm-records)
    records_service = None

    site_metadata_attr = "site_metadata"

    supported_formats = {
        # Existing JSON-LD validation via jsonschema
        "jsonld": {
            "validator": JSONSchemaValidator(
                {
                    "type": "object",
                    "properties": {
                        "@context": {},
                        "@type": {"type": ["string", "array"]},
                    },
                    "required": ["@type"],
                }
            ),
            "index_name": "site-metadata-jsonld",
        },
        # NEW: Plain JSON validation via Marshmallow
        "json": {
            "validator": MarshmallowValidator(JSONMetadataSchema()),
            "index_name": "site-metadata-json",
        },
    }
