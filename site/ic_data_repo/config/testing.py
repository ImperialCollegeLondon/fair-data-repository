"""Settings file for testing."""

from .settings import *  # noqa: F401, F403

SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"

# blank out sqlalchemy options as the defaults (inherited from
# invenio_app_rdm.config) contain "pool_timeout" which is not valid for use with
# the test sqlite database
SQLALCHEMY_ENGINE_OPTIONS = ""
