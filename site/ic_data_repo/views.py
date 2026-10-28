"""Additional views."""

from flask import Blueprint, abort
from flask_login import login_required
from invenio_oauthclient.views.client import _login as _oauthclient_login

from .auth.orcid import linked_orcid_id, orcid_linking_available


@login_required
def connect_orcid():
    """Start the ORCID linking flow for the current, already-authenticated user."""
    if not orcid_linking_available():
        abort(404)

    return _oauthclient_login("orcid", "invenio_oauthclient.authorized")


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

    # Template helpers for the Linked Accounts page
    blueprint.add_app_template_global(orcid_linking_available)
    blueprint.add_app_template_global(linked_orcid_id)

    return blueprint
