"""Settings file targeting production deployments."""

import os

from .settings import *  # noqa: F401, F403

SECRET_KEY = os.environ["INVENIO_SECRET_KEY"]

TRUSTED_HOSTS = os.environ["INVENIO_TRUSTED_HOSTS"].split(",")
SITE_UI_URL = f"https://{TRUSTED_HOSTS[0]}"
SITE_API_URL = f"https://{TRUSTED_HOSTS[0]}/api"

ACCOUNTS_LOCAL_LOGIN_ENABLED = False

MAIL_SUPPRESS_SEND = False

SUPPORT_CONTACT_EMAIL = "rdm-enquiries@ic.ac.uk"
