"""Site Metadata resource configuration."""

from flask_resources import ResourceConfig, ResponseHandler
from flask_resources.serializers import JSONSerializer


class SiteMetadataResourceConfig(ResourceConfig):
    """Site Metadata resource configuration."""

    blueprint_name = "site-metadata"
    url_prefix = "/records"
    routes = {
        # Full path: /records/<pid_value>/metadata/<fmt>
        "upload_validate": "/<pid_value>/metadata/<fmt>",
    }
    response_handlers = {
        "application/json": ResponseHandler(JSONSerializer()),
    }
