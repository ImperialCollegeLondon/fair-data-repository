"""ORCID account linking handlers."""

from flask import flash, redirect, url_for
from flask_login import current_user
from invenio_i18n import lazy_gettext as _
from invenio_oauthclient.errors import (
    OAuthClientUnAuthorized,
    OAuthRejectedRequestError,
)
from invenio_oauthclient.handlers import oauth_error_handler
from invenio_oauthclient.handlers.authorized import authorized_handler as _authorized


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
