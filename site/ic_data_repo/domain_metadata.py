"""Custom field for domain metadata: a list of {id, value} pairs.

``id`` must reference an existing term in the "domainmetadatascheme"
vocabulary; ``value`` is required free-text subject content supplied by the
client, independent of the vocabulary term itself.
"""

from invenio_pidstore.errors import PersistentIdentifierError
from invenio_records_resources.services.custom_fields.base import BaseCF
from invenio_vocabularies.records.api import Vocabulary
from marshmallow import Schema, ValidationError, fields, validate, validates
from marshmallow_utils.fields import SanitizedUnicode


def _resolve_domain_metadata_scheme(id_):
    """Resolve a "domainmetadatascheme" vocabulary term by id, or None."""
    if not id_:
        return None
    try:
        return Vocabulary.pid.with_type_ctx("domainmetadatascheme").resolve(id_)
    except PersistentIdentifierError:
        return None


class DomainMetadataItemSchema(Schema):
    """Schema for a single {id, value} domain metadata pair."""

    id = SanitizedUnicode(required=True)
    value = SanitizedUnicode(required=True, validate=validate.Length(min=1))

    @validates("id")
    def validate_id(self, value, **kwargs):
        """Reject ids that don't resolve to a real vocabulary term."""
        if _resolve_domain_metadata_scheme(value) is None:
            raise ValidationError("Invalid domain metadata scheme id.")


class DomainMetadataCF(BaseCF):
    """Custom field for domain metadata: a list of {id, value} pairs."""

    @property
    def field(self):
        """Marshmallow field: a list of {id, value} pairs."""
        return fields.List(fields.Nested(DomainMetadataItemSchema), **self._field_args)

    @property
    def mapping(self):
        """OpenSearch mapping."""
        return {
            "type": "object",
            "properties": {
                "id": {"type": "keyword"},
                "value": {"type": "keyword"},
            },
        }
