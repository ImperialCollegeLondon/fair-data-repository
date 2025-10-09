"""Site Metadata service errors."""


class SiteMetadataError(Exception):
    """Base metadata service error."""


class UnsupportedFormatError(SiteMetadataError):
    """Unsupported metadata format error."""

    def __init__(self, fmt):
        """Constructor."""
        super().__init__(f"Unsupported metadata format '{fmt}'")
        self.fmt = fmt


class MetadataValidationError(SiteMetadataError):
    """Metadata validation error."""

    def __init__(self, fmt, errors):
        """Constructor."""
        super().__init__(f"Validation failed for '{fmt}'")
        self.fmt = fmt
        self.errors = errors


class MetadataFileNotFoundError(SiteMetadataError):
    """Metadata file not found error."""

    def __init__(self, file_key):
        """Constructor."""
        super().__init__(f"Metadata file not found: {file_key}")
        self.file_key = file_key
