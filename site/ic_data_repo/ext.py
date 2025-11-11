"""Imperial College Data Repository Extension."""

import asyncio

from flask import g
from flask_login import user_logged_in
from ic_data_repo.site_metadata.resources.config import SiteMetadataResourceConfig
from ic_data_repo.site_metadata.resources.resource import SiteMetadataResource
from ic_data_repo.site_metadata.services.config import SiteMetadataServiceConfig
from ic_data_repo.site_metadata.services.schema import (
    JSONMetadataSchema,
    MarshmallowValidator,
)
from ic_data_repo.site_metadata.services.service import SiteMetadataService
from ic_data_repo.symplectic.resources.config import SymplecticResourceConfig
from ic_data_repo.symplectic.resources.resource import SymplecticResource
from ic_data_repo.symplectic.services.config import SymplecticServiceConfig
from ic_data_repo.symplectic.services.service import SymplecticService
from invenio_access.permissions import ActionUsers
from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records
from jinja2 import nodes
from jinja2.ext import Extension
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

from .microsoft_graph_api_client import get_client
from .permissions import can_user_deposit, deposit_action


class IfUserCanTag(Extension):
    """Jinja2 tag to check if a user can do things in templates."""

    tags = {"if_user_can"}

    def parse(self, parser):
        """Parse user permission check tags.

        Example usage in a template:
        {% if_user_can "permission_1", "permission_2", ... %}
          <p>Content for users with all required permissions.</p>
        {% else %}
          <p>Content for everyone else.</p>
        {% end_if_user_can %}
        """
        lineno = next(parser.stream).lineno

        # parse the permissions and check the user.
        args = [parser.parse_expression()]
        while parser.stream.skip_if("comma"):
            args.append(parser.parse_expression())
        check_call = self.call_method("_check_permissions", args)

        # if body.
        body_if = parser.parse_statements(
            ("name:else", "name:end_if_user_can"),
            drop_needle=False,
        )

        # elif body is not used.
        body_elif = []

        # else body, if present.
        body_else = []
        if parser.stream.current.test("name:else"):
            next(parser.stream)  # consume 'else'
            body_else = parser.parse_statements(
                ("name:end_if_user_can",),
                drop_needle=True,
            )
        else:
            # Still need to consume the end tag if no else is present.
            parser.stream.expect("name:end_if_user_can")

        return nodes.If(check_call, body_if, body_elif, body_else).set_lineno(lineno)

    def _check_permissions(self, *permissions):
        """Check if the user has all the specified permissions."""
        identity = g.identity
        service = current_rdm_records.records_service
        return all(service.check_permission(identity, p) for p in permissions)


class ImperialExtension:
    """Imperial College Data Repository Extension class.

    Registered for loading by Invenio via entrypoint.
    """

    def __init__(self, app=None):
        """Initialise the extension."""
        if not app:
            return

        @user_logged_in.connect_via(app)
        def grant_deposit_permission(sender, user):
            """Signal handler to grant deposit permission based on user attributes."""
            # abort if access to the graph api is not enabled
            if not app.config["ICL_GRAPH_API_ENABLED"]:
                return

            # abort if the user already has permission to deposit
            if (
                ActionUsers.query_by_action(deposit_action)
                .filter(ActionUsers.user_id == user.id)
                .count()
            ):
                return

            # get identity data from microsoft graph api
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
                select=["onPremisesExtensionAttributes"]
            )
            request_config = RequestConfiguration(query_parameters=query_params)
            client = get_client(
                app.config["ICL_MICROSOFT_TENANT_ID"],
                app.config["ICL_OAUTH_CLIENT_ID"],
                app.config["ICL_OAUTH_CLIENT_SECRET"],
            )

            try:
                extension_attributes = asyncio.run(
                    client.users.by_user_id(f"{user.username}@ic.ac.uk").get(
                        request_config
                    )
                ).on_premises_extension_attributes
            except ODataError as e:
                if e.response_status_code == 404:
                    # this situation should only come up in development
                    # when using a locally created user
                    app.logger.exception(e)
                    return
                else:
                    raise

            # determine if user should be able to deposit based on their attributes
            if can_user_deposit(
                role_type=extension_attributes.extension_attribute6,
                job_family=extension_attributes.extension_attribute10,
            ):
                with db.session.begin_nested():
                    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))
                db.session.commit()

        # Register jinja2 extension for user permission checks.
        app.jinja_env.add_extension(IfUserCanTag)


class SymplecticExt:
    """Extension for Symplectic API interactions."""

    def __init__(self, app=None):
        """Initialize the Symplectic extension."""
        self.service = None
        self.resource = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the extension with the Flask app."""
        self.init_config(app)
        self.init_service(app)
        self.init_resource(app)
        app.extensions["symplectic"] = self

    def init_config(self, app):
        """Initialize configuration for the Symplectic extension."""
        app.config.setdefault("SYMPLECTIC_API_URL", "")
        app.config.setdefault("SYMPLECTIC_API_SUBSCRIPTION_KEY", "")

    def init_service(self, app):
        """Initialize service."""
        service_config = SymplecticServiceConfig.build(app)
        self.service = SymplecticService(service_config)

    def init_resource(self, app):
        """Initialize resource."""
        resource_config = SymplecticResourceConfig()
        self.resource = SymplecticResource(resource_config, self.service)

        # Register blueprint
        app.register_blueprint(self.resource.as_blueprint())


class SiteMetadataExt:
    """Extension for per-format metadata upload/validation and publish-time indexing."""

    def __init__(self, app=None):
        """Initialize the Site Metadata extension."""
        self.service = None
        self.resource = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the extension with the Flask app."""
        self.init_config(app)
        self.init_service(app)
        self.init_resource(app)
        app.extensions["site-metadata"] = self

    def init_config(self, app):
        """Initialize configuration for the Site Metadata extension."""
        app.config.setdefault("IC_SITE_METADATA_ATTR", "site_metadata")
        app.config.setdefault("IC_SITE_METADATA_FORMATS", None)

    def init_service(self, app):
        """Initialize service."""
        cfg = SiteMetadataServiceConfig()

        cfg._get_records_service = lambda: current_rdm_records.records_service
        cfg.site_metadata_attr = app.config["IC_SITE_METADATA_ATTR"]

        if not getattr(cfg, "supported_formats", None):
            cfg.supported_formats = {}
        if "json" not in cfg.supported_formats:
            cfg.supported_formats["json"] = {
                "validator": MarshmallowValidator(JSONMetadataSchema()),
                "index_name": "site-metadata-json",
            }

        runtime_formats = app.config.get("IC_SITE_METADATA_FORMATS")
        if runtime_formats:
            cfg.supported_formats.update(runtime_formats)

        self.service = SiteMetadataService(cfg)

    def init_resource(self, app):
        """Initialize resource."""
        res_cfg = SiteMetadataResourceConfig()
        self.resource = SiteMetadataResource(res_cfg, self.service)
        app.register_blueprint(self.resource.as_blueprint())
