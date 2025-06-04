"""Imperial College Data Repository Extension."""

import asyncio

from flask import g
from flask_login import user_logged_in
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
        {% end_if_user_can %}
        """
        lineno = next(parser.stream).lineno
        args = [parser.parse_expression()]
        while parser.stream.skip_if("comma"):
            args.append(parser.parse_expression())
        body = parser.parse_statements(("name:end_if_user_can",), drop_needle=True)
        check_call = self.call_method("_check_permissions", args)
        return nodes.If(check_call, body, [], []).set_lineno(lineno)

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
