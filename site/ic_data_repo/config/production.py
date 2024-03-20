"""Settings file targeting production deployments."""

import os

from .settings import *  # noqa: F401, F403

SECRET_KEY = os.environ["INVENIO_SECRET_KEY"]

APP_ALLOWED_HOSTS = os.environ["INVENIO_APP_ALLOWED_HOSTS"].split(",")
SITE_UI_URL = f"https://{APP_ALLOWED_HOSTS[0]}"
SITE_API_URL = f"https://{APP_ALLOWED_HOSTS[0]}/api"

SSO_SAML_IDPS["icl"]["settings"]["debug"] = False  # noqa: F405

ACCOUNTS_LOCAL_LOGIN_ENABLED = False
