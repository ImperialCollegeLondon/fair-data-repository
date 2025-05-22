"""InvenioRDM Imperial Metadata Schema.

This schema aligns with the record submission form customisations.

"""

from flask import current_app
from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.services.schemas import MetadataSchema
from invenio_rdm_records.services.schemas.access import AccessSchema
from invenio_rdm_records.services.schemas.metadata import CreatorSchema, ReferenceSchema
from invenio_vocabularies.services.schema import VocabularyRelationSchema
from marshmallow import validate
from marshmallow.fields import List, Nested, String
from marshmallow_utils.fields import SanitizedHTML
from werkzeug.local import LocalProxy


class CreatorsValue(List):
    """Creatibutor stripped of role if it exists."""

    def deserialize(self, value, attr=None, data=None, **kwargs):
        """Remove role from creator."""
        if value:
            for creator in value:
                if "role" in creator:
                    del creator["role"]
        return super().deserialize(value, attr, data, **kwargs)


class ReferenceValue(List):
    """Empty references regardless of input."""

    def deserialize(self, value, attr=None, data=None, **kwargs):
        """Return empty list."""
        return []


class ResourceValue(Nested):
    """Resource type set to default from config."""

    def deserialize(self, value, attr=None, data=None, **kwargs):
        """Return default resource type."""
        resource_type = current_app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"][
            "resource_type"
        ]
        return {"id": str(resource_type)}


class PublisherValue(String):
    """Publisher set to default from config."""

    def deserialize(self, value, attr=None, data=None, **kwargs):
        """Return default publisher."""
        return current_app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"]["publisher"]


class PublicationDateValue(String):
    """Publication date set to default from config."""

    def deserialize(self, value, attr=None, data=None, **kwargs):
        """Return the date today."""
        return LocalProxy(
            lambda: current_app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"][
                "publication_date"
            ]()
        )


class ImperialMetadataSchema(MetadataSchema):
    """Imperial Metadata Schema that overrides five fields."""

    resource_type = ResourceValue(VocabularyRelationSchema, required=True)
    creators = CreatorsValue(
        Nested(CreatorSchema),
        required=True,
        validate=validate.Length(min=1, error=_("Missing data for required field.")),
    )
    description = SanitizedHTML(required=True, validate=validate.Length(min=3))
    publisher = PublisherValue()
    publication_date = PublicationDateValue(
        load_default=lambda: current_app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"][
            "publication_date"
        ]()
    )
    references = ReferenceValue(Nested(ReferenceSchema))


class PublicRecordProtectionValue(String):
    """Record protection fixed to public."""

    def deserialize(self, value, attr=None, data=None, **kwargs):
        """Return record protection fixed to public."""
        return "public"


class ImperialAccessSchema(AccessSchema):
    """Imperial Access Schema."""

    record = PublicRecordProtectionValue(required=True)
