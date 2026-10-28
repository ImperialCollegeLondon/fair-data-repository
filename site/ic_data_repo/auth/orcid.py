"""ORCID account linking handlers."""

from flask import current_app, flash, redirect, url_for
from flask_login import current_user
from invenio_accounts.models import UserIdentity
from invenio_i18n import lazy_gettext as _
from invenio_oauthclient.errors import (
    OAuthClientUnAuthorized,
    OAuthRejectedRequestError,
)
from invenio_oauthclient.handlers import oauth_error_handler
from invenio_oauthclient.handlers.authorized import authorized_handler as _authorized
from invenio_oauthclient.proxies import current_oauthclient


def orcid_linking_available():
    """Return whether ORCID linking is configured and its remote app registered."""
    return current_app.config.get("ORCID_OAUTH_ENABLED") and (
        "orcid" in current_oauthclient.oauth.remote_apps
    )


def linked_orcid_id():
    """Return the ORCID iD the current user has linked, if any."""
    if not current_user.is_authenticated:
        return None

    identity = UserIdentity.query.filter_by(
        id_user=current_user.id, method="orcid"
    ).first()
    return identity.id if identity else None


@oauth_error_handler
def authorized_handler(resp, remote, *args, **kwargs):
    """Link ORCID to the logged-in user, then return to the Linked Accounts page."""
    if not current_user.is_authenticated:
        raise OAuthClientUnAuthorized()

    try:
        _authorized(resp, remote, *args, **kwargs)
    except OAuthRejectedRequestError:
        flash(_("ORCID linking was cancelled."), category="info")
    else:
        flash(_("Your ORCID iD has been linked."), category="success")

    return redirect(url_for("invenio_oauthclient_settings.index"))
