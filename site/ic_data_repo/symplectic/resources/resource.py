"""Imperial College Data Repository Symplectic Resource."""

import marshmallow as ma
from flask import g
from flask_resources import (
    HTTPJSONException,
    Resource,
    create_error_handler,
    resource_requestctx,
    response_handler,
    route,
)
from flask_resources.parsers import request_parser

from ..services.errors import SymplecticServiceError


class SymplecticResource(Resource):
    """Resource for Symplectic API interactions."""

    # Map service errors to HTTP errors
    error_handlers = {
        SymplecticServiceError: create_error_handler(
            HTTPJSONException(
                code=500,
                description="Symplectic API error.",
            )
        )
    }

    def __init__(self, config, service):
        """Initialize the Symplectic resource."""
        super().__init__(config)
        self.service = service

    def create_url_rules(self):
        """Create URL rules for the resource."""
        routes = self.config.routes
        return [
            route("GET", routes["related_objects"], self.get_related_objects),
        ]

    @request_parser({"doi": ma.fields.String(required=True)}, location="args")
    @response_handler()
    def get_related_objects(self):
        """Get related objects for a DOI."""
        # Get validated DOI from request context
        doi = resource_requestctx.args["doi"]
        # Call the service with flask identity
        result = self.service.fetch_related_objects(g.identity, doi)

        # Return the result dictionary with HTTP 200 status
        return result.to_dict(), 200

        # Return the result as a dictionary
        return result.to_dict(), 200
