"""Custom field for domain metadata: a list of {id, value} pairs.

``id`` must reference an existing term in the "domainmetadatascheme"
vocabulary; ``value`` is required free-text subject content supplied by the
client, independent of the vocabulary term itself.
"""

from invenio_pidstore.errors import PersistentIdentifierError
from invenio_records_resources.services.custom_fields.base import BaseCF
from invenio_vocabularies.records.api import Vocabulary
from marshmallow import Schema, ValidationError, fields, post_dump, validate, validates
from marshmallow_utils.fields import SanitizedUnicode


def _resolve_domain_metadata_scheme(id_):
    """Resolve a "domainmetadatascheme" vocabulary term by id, or None."""
    if not id_:
        return None
    try:
        return Vocabulary.pid.with_type_ctx("domainmetadatascheme").resolve(id_)
    except PersistentIdentifierError:
        return None


def _safe_uri(uri):
    """Only pass through http(s) URIs -- vocabulary props are free-text data
    entered via fixture files, not schema-constrained, so a landing-page link
    built from them must not blindly trust the scheme (e.g. javascript:).
    """
    return (
        uri
        if isinstance(uri, str) and uri.startswith(("http://", "https://"))
        else None
    )


class DomainMetadataItemSchema(Schema):
    """Schema for a single {id, value} domain metadata pair."""

    id = SanitizedUnicode(required=True)
    value = SanitizedUnicode(required=True, validate=validate.Length(min=1))

    @validates("id")
    def validate_id(self, value, **kwargs):
        """Reject ids that don't resolve to a real vocabulary term."""
        if _resolve_domain_metadata_scheme(value) is None:
            raise ValidationError("Invalid domain metadata scheme id.")


class DomainMetadataItemUISchema(DomainMetadataItemSchema):
    """Landing-page dump of a {id, value} pair: adds the resolved vocabulary
    term's title and (safe, http(s)-only) DataCite-style scheme/value URIs,
    read-only, alongside the stored id/value. Never used for input -
    @validates only runs on load(), so inheriting it here is harmless.
    """

    @post_dump
    def add_resolved_vocabulary(self, data, **kwargs):
        """Attach the resolved vocabulary term's title/props, if it still resolves."""
        term = _resolve_domain_metadata_scheme(data.get("id"))
        if term is None:
            return data

        title = term.get("title") or {}
        data["title"] = title.get("en") or next(iter(title.values()), None)

        props = term.get("props") or {}
        data["props"] = {
            "subjectScheme": props.get("subjectScheme"),
            "schemeURI": _safe_uri(props.get("schemeURI")),
            "valueURI": _safe_uri(props.get("valueURI")),
        }
        return data


class DomainMetadataCF(BaseCF):
    """Custom field for domain metadata: a list of {id, value} pairs."""

    @property
    def field(self):
        """Marshmallow field: a list of {id, value} pairs."""
        return fields.List(fields.Nested(DomainMetadataItemSchema), **self._field_args)

    @property
    def ui_field(self):
        """Marshmallow UI field: as `field`, but each entry also carries the
        resolved vocabulary term's title/props for landing-page display (see
        DomainMetadataItemUISchema) - the stored id/value themselves are
        untouched, this only adds extra read-only display data.
        """
        return fields.List(
            fields.Nested(DomainMetadataItemUISchema), **self._field_args
        )

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
