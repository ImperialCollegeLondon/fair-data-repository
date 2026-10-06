"""Additional views."""

from flask import Blueprint, abort, current_app
from flask_login import current_user, login_required
from invenio_accounts.models import UserIdentity
from invenio_oauthclient.proxies import current_oauthclient
from invenio_oauthclient.views.client import _login as _oauthclient_login


def orcid_linking_available():
    """Return whether ORCID linking is configured and its remote app registered."""
    return bool(current_app.config.get("ORCID_OAUTH_ENABLED")) and (
        "orcid" in current_oauthclient.oauth.remote_apps
    )


@login_required
def connect_orcid():
    """Start the ORCID linking flow for the current, already-authenticated user."""
    if not orcid_linking_available():
        abort(404)

    return _oauthclient_login("orcid", "invenio_oauthclient.authorized")


def linked_orcid_id():
    """Return the ORCID iD the current user has linked, if any."""
    if not current_user.is_authenticated:
        return None

    identity = UserIdentity.query.filter_by(
        id_user=current_user.id, method="orcid"
    ).first()
    return identity.id if identity else None


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
