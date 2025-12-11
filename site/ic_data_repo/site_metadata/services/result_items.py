"""Site Metadata service result items."""

from invenio_records_resources.services.base import ServiceItemResult


class MetadataValidationResult(ServiceItemResult):
    """Metadata validation result item."""

    def __init__(self, identity, record_id, fmt, file_key, valid, errors=None):
        """Constructor."""
        self._identity = identity
        self.record_id = str(record_id)
        self.fmt = fmt
        self.file_key = file_key
        self.valid = valid
        self.errors = errors or []

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "format": self.fmt,
            "file_key": self.file_key,
            "valid": self.valid,
            "errors": self.errors,
        }
