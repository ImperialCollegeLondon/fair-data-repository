"""InvenioRDM Imperial Metadata Schema.

This schema aligns with the record submission form customisations.

"""

import typing

from flask import current_app
from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.services.schemas import MetadataSchema
from invenio_rdm_records.services.schemas.metadata import CreatorSchema, ReferenceSchema
from invenio_vocabularies.services.schema import VocabularyRelationSchema
from marshmallow import validate
from marshmallow.fields import List, Nested, String
from werkzeug.local import LocalProxy


class CreatorsValue(List):
    """Creatibutor stripped of role if it exists."""

    def _deserialize(self, value, attr, data, **kwargs) -> typing.Any:
        for creator in value:
            if "role" in creator:
                del creator["role"]
        return super()._deserialize(value, attr, data, **kwargs)


class ReferenceValue(List):
    """Empty references regardless of input."""

    def _deserialize(self, value, attr, data, **kwargs) -> typing.Any:
        return []


class ResourceValue(Nested):
    """Resource type set to default from config."""

    def _deserialize(
        self,
        value: typing.Any,
        attr: typing.Optional[str],
        data: typing.Optional[typing.Mapping[str, typing.Any]] = None,
        partial: typing.Union[
            bool, typing.Union[typing.Sequence[str], typing.AbstractSet[str]], None
        ] = None,
        **kwargs: typing.Any
    ) -> typing.Any:
        resource_type = current_app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"][
            "resource_type"
        ]
        return {"id": str(resource_type)}


class PublisherValue(String):
    """Publisher set to default from config."""

    def _deserialize(self, value, attr, data, **kwargs) -> typing.Any:
        return current_app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"]["publisher"]


class PublicationDateValue(String):
    """Publication date set to default from config."""

    def _deserialize(self, value, attr, data, **kwargs) -> typing.Any:
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
    publisher = PublisherValue()
    publication_date = PublicationDateValue(
        load_default=lambda: current_app.config["APP_RDM_DEPOSIT_FORM_DEFAULTS"][
            "publication_date"
        ]()
    )
    references = ReferenceValue(Nested(ReferenceSchema))
