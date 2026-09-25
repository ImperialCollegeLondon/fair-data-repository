"""Additional views."""

from flask import Blueprint, abort, current_app
from flask_login import login_required
from invenio_oauthclient.errors import OAuthRemoteNotFound
from invenio_oauthclient.views.client import _login as _oauthclient_login


@login_required
def connect_orcid():
    """Start the ORCID linking flow for the current, already-authenticated user."""
    if not current_app.config.get("ORCID_OAUTH_ENABLED"):
        abort(404)

    try:
        return _oauthclient_login("orcid", "invenio_oauthclient.authorized")
    except OAuthRemoteNotFound:
        abort(404)


#
# Registration
#
def create_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "ic_data_repo",
        __name__,
        template_folder="./templates",
    )

    # Add URL rules
    blueprint.add_url_rule(
        "/account/settings/orcid/connect",
        view_func=connect_orcid,
        endpoint="connect_orcid",
    )

    return blueprint
