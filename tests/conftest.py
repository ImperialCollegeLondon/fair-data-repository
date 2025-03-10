"""Global test fixtures."""

import os
from pathlib import Path

import pytest
from invenio_app.factory import create_app as app_factory


@pytest.fixture(scope="module")
def app_config(app_config):
    """Update invenio app_config fixture."""
    from ic_data_repo.config import settings

    # blank out sqlalchemy options as the defaults (inherited from
    # invenio_app_rdm.config) contain "pool_timeout" which is not valid for use with
    # the test sqlite database
    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = ""
    return settings.__dict__ | app_config


@pytest.fixture(scope="module")
def create_app():
    """Provide the Flask app object used by tests."""
    return app_factory


@pytest.fixture(scope="module")
def instance_path(instance_path):
    """Extend the instance_path fixture to project templates.

    This PR makes our overriden templates at the project level available within the
    temporary instance directory used by the tests via symlink.
    """
    src_dir = Path(__file__).resolve().parent.parent / "templates"
    dest_dir = Path(instance_path) / "templates"
    os.symlink(src_dir, dest_dir)
    yield instance_path
