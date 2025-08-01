"""Imperial College Data Repository Symplectic Service Errors."""


class SymplecticServiceError(Exception):
    """Base exception for Symplectic service errors."""

    pass


class InvalidDOIError(SymplecticServiceError):
    """Raised when an invalid DOI is provided."""

    pass


class SymplecticAPIError(SymplecticServiceError):
    """Raised when the Symplectic API returns an error."""

    pass
