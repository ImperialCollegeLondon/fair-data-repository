"""Site Metadata service schema and validators."""

import json

from marshmallow import Schema
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields


class MarshmallowValidator:
    """Marshmallow-based validator callable."""

    def __init__(self, schema: Schema):
        """Constructor."""
        self.schema = schema

    def __call__(self, raw: bytes):
        """Validate the raw bytes and return the parsed/loaded data."""
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as ex:
            raise ValueError(f"Invalid JSON: {ex}")

        try:
            return self.schema.load(data)
        except MarshmallowValidationError as ve:
            # Convert to ValueError for service error normalization
            raise ValueError(ve.messages or str(ve))


class JSONMetadataSchema(Schema):
    """Example site JSON metadata schema."""

    name = fields.String(required=True)
    description = fields.String()
    version = fields.String()
    type = fields.String()


def build_validators(spec):
    """Build validators from the specification."""
    return {fmt: cfg["validator"] for fmt, cfg in spec.items()}
