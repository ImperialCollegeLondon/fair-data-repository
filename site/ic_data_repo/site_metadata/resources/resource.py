"""Site Metadata resource layer."""

from flask import g, request
from flask_resources import (
    HTTPJSONException,
    Resource,
    create_error_handler,
    response_handler,
    route,
)

from ..services.errors import MetadataValidationError, UnsupportedFormatError
from .config import SiteMetadataResourceConfig


class SiteMetadataResource(Resource):
    """Site Metadata resource."""

    error_handlers = {
        MetadataValidationError: create_error_handler(
            HTTPJSONException(code=400, description="Metadata validation failed.")
        ),
        UnsupportedFormatError: create_error_handler(
            HTTPJSONException(code=400, description="Unsupported metadata format.")
        ),
    }

    def __init__(self, config: SiteMetadataResourceConfig, service):
        """Constructor."""
        super().__init__(config)
        self.service = service

    def create_url_rules(self):
        """Create URL routes for the resource."""
        routes = self.config.routes
        return [
            route("POST", routes["upload_validate"], self.upload_validate),
        ]

    @response_handler()
    def upload_validate(self, pid_value, fmt):
        """Upload and validate metadata file."""
        if "file" not in request.files:
            return {"message": "Missing file field 'file'."}, 400
        f = request.files["file"]
        result = self.service.upload_and_validate(
            g.identity,
            pid_value,
            fmt,
            f.stream,
            f.filename,
        )
        return result.to_dict(), 200
