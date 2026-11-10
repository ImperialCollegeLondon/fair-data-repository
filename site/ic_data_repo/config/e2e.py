"""Configuration for a local application serving Selenium e2e tests."""

from invenio_app.config import RATELIMIT_PER_ENDPOINT as DEFAULT_ENDPOINT_LIMITS

from .settings import *  # noqa: F403

RATELIMIT_PER_ENDPOINT = {
    **DEFAULT_ENDPOINT_LIMITS,
    "security.login": "100 per minute",
}
