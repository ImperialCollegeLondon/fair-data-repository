"""Imperial College Data Repository Symplectic Resource."""

from typing import ClassVar

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
    error_handlers: ClassVar = {
        SymplecticServiceError: create_error_handler(
            HTTPJSONException(
                code=500,
                description="Symplectic API error.",
            )
        ),
        ma.exceptions.ValidationError: create_error_handler(
            lambda e: HTTPJSONException(
                code=400,
                description="Invalid request parameters.",
                errors=e.messages,
            )
        ),
    }

    def __init__(self, config, service):
        """Initialize the Symplectic resource."""
        super().__init__(config)
        self.service = service

    def create_url_rules(self):
        """Create URL rules for the resource."""
        routes = self.config.routes
        return [
            route("GET", routes["related_publications"], self.get_related_publications),
        ]

    @request_parser(
        {
            "search_query": ma.fields.String(required=True),
            "search_type": ma.fields.String(
                required=True,
                validate=ma.validate.OneOf(
                    ["title-keywords", "first-author-name"]
                ),  # Add valid search types
            ),
        },
        location="args",
    )
    @response_handler()
    def get_related_publications(self):
        """Get related objects for a DOI."""
        # Get validated DOI from request context
        search_query = resource_requestctx.args["search_query"]
        search_type = resource_requestctx.args["search_type"]
        # Call the service with flask identity
        result = self.service.fetch_related_publications(
            g.identity, search_query, search_type
        )

        # Return the result dictionary with HTTP 200 status
        return result.to_dict(), 200
