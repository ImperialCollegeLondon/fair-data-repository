"""Site Metadata service schema and validators."""

import json

import jsonschema


class JSONSchemaValidator:
    """JSON schema validator callable."""

    def __init__(self, schema):
        """Constructor."""
        if jsonschema is None:
            raise RuntimeError("jsonschema must be installed for JSON validation")
        self.schema = schema

    def __call__(self, raw: bytes):
        """Validate the raw bytes and return the parsed data."""
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as ex:
            raise ValueError(f"Invalid JSON: {ex}")
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as ve:
            raise ValueError(ve.message)
        return data


def build_validators(spec):
    """Build validators from the specification."""
    return {fmt: cfg["validator"] for fmt, cfg in spec.items()}
