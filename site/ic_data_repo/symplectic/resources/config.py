"""Configuration for the Symplectic resource in the Imperial College Data Repository."""

from typing import ClassVar

from flask_resources import ResourceConfig, ResponseHandler
from flask_resources.serializers import JSONSerializer


class SymplecticResourceConfig(ResourceConfig):
    """Configuration for the Symplectic resource."""

    blueprint_name = "symplectic"
    url_prefix = "/symplectic"

    routes: ClassVar = {
        "related_publications": "/related-publications",
    }

    # Content negotiation configuration
    response_handlers: ClassVar = {
        "application/json": ResponseHandler(JSONSerializer()),
        "default": ResponseHandler(JSONSerializer()),
    }
