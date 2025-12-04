"""Imperial College Data Repository Symplectic Service Errors."""


class SymplecticServiceError(Exception):
    """Base exception for Symplectic service errors."""


class InvalidDOIError(SymplecticServiceError):
    """Raised when an invalid DOI is provided."""


class SymplecticAPIError(SymplecticServiceError):
    """Raised when the Symplectic API returns an error."""
