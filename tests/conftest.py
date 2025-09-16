"""Global test fixtures."""

import json
import os
from pathlib import Path

import pytest
import redis
from invenio_access.permissions import system_identity
from invenio_app.factory import create_app as app_factory
from invenio_rdm_records.fixtures.vocabularies import VocabulariesFixture


@pytest.fixture(scope="session")
def opensearch_container():
    """Start an OpenSearch container."""
    from testcontainers.opensearch import OpenSearchContainer

    with OpenSearchContainer("opensearchproject/opensearch:2.18.0") as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(9200)

        # settings only for development. DO NOT use in production!
        container.with_env("bootstrap.memory_lock", "true")
        container.with_env("OPENSEARCH_JAVA_OPTS", "-Xms512m -Xmx512m")
        container.with_env("DISABLE_INSTALL_DEMO_CONFIG", "true")
        container.with_env("DISABLE_SECURITY_PLUGIN", "true")
        container.with_env("discovery.type", "single-node")

        yield {"host": host, "port": port}


@pytest.fixture(scope="session")
def redis_container():
    """Start a Redis container."""
    from testcontainers.redis import RedisContainer

    with RedisContainer() as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6379)

        yield {"host": host, "port": port}


@pytest.fixture(scope="module")
def app_config(opensearch_container, redis_container, app_config):
    """Update invenio app_config fixture for Redis/OpenSearch and webpack configs."""
    from ic_data_repo.config import settings

    # blank out sqlalchemy options as the defaults (inherited from
    # invenio_app_rdm.config) contain "pool_timeout" which is not valid for use with
    # the test sqlite database
    app_config["SQLALCHEMY_ENGINE_OPTIONS"] = ""

    # OpenSearch config.
    opensearch_host = opensearch_container["host"]
    opensearch_port = opensearch_container["port"]
    app_config["SEARCH_HOSTS"] = [{"host": opensearch_host, "port": opensearch_port}]

    # Redis config.
    redis_host = redis_container["host"]
    redis_port = redis_container["port"]
    redis_url = f"redis://{redis_host}:{redis_port}"
    app_config["CACHE_TYPE"] = "redis"
    app_config["CACHE_REDIS_URL"] = f"{redis_url}/0"
    app_config["IIIF_CACHE_REDIS_URL"] = f"{redis_url}/0"
    app_config["ACCOUNTS_SESSION_REDIS_URL"] = f"{redis_url}/1"
    app_config["CELERY_RESULT_BACKEND"] = f"{redis_url}/2"
    app_config["RATELIMIT_STORAGE_URL"] = f"{redis_url}/3"
    app_config["COMMUNITIES_IDENTITIES_CACHE_REDIS_URL"] = f"{redis_url}/4"

    # ---- Webpack manifest configuration ----
    app_config["COLLECT_STORAGE"] = "flask_collect.storage.file"
    instance_path = app_config.get(
        "INSTANCE_PATH", os.environ.get("INVENIO_INSTANCE_PATH", "/tmp")
    )
    manifest_dir = os.path.join(instance_path, "static/dist")
    manifest_path = os.path.join(manifest_dir, "manifest.json")
    os.makedirs(manifest_dir, exist_ok=True)

    with open(manifest_path, "w") as f:
        json.dump(
            {
                "status": "done",
                "assets": {"theme.css": "/static/dist/theme.css"},
                "chunks": {},
                "publicPath": "/static/dist",
            },
            f,
        )

    theme_css_path = os.path.join(manifest_dir, "theme.css")
    with open(theme_css_path, "w") as f:
        f.write("/* Empty theme file */")

    app_config["WEBPACKEXT_MANIFEST_PATH"] = manifest_path
    # Let us create records without files for testing purposes.
    app_config["RDM_ALLOW_METADATA_ONLY_RECORDS"] = True

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


@pytest.fixture
def vocabularies(db):
    """Load vocabularies."""
    vocabularies = VocabulariesFixture(
        system_identity,
        Path(__file__).parent / "data/vocabularies.yaml",
        delay=False,
    )
    vocabularies.load()


@pytest.fixture
def flush_redis(redis_container):
    """Remove all data from redis.

    This fixture can be used to flush all data from the redis after a test is run.
    Some invenio features, notably the permission system, persist data in the cache
    which can cause contamination between tests.
    """
    yield
    for i in range(5):
        client = redis.Redis(
            host=redis_container["host"], port=redis_container["port"], db=i
        )
        client.flushdb()


@pytest.fixture
def app(app, flush_redis):
    """Override the existing app fixture to add flush_redis teardown."""
    return app


@pytest.fixture
def user(UserFixture, app, db):
    """An initialised user."""
    u = UserFixture(
        email="foo@bar.com",
        password="password",
    )
    u.create(app, db)
    return u


@pytest.fixture
def user_client(user, client):
    """A client logged in as the user fixture."""
    return user.login(client)


@pytest.fixture
def db(database, db_session_options):
    """Creates a new database session for a test, rolls back after test."""
    from flask_sqlalchemy.session import Session as FlaskSQLAlchemySession

    connection = database.engine.connect()
    transaction = connection.begin()  # Outer transaction

    class PytestInvenioSession(FlaskSQLAlchemySession):
        def commit(self, *args, **kwargs):
            # prevent any commits to the outer session
            self.flush(*args, **kwargs)

    options = dict(
        bind=connection,
        binds={},
        **db_session_options,
        class_=PytestInvenioSession,
    )
    session = database._make_scoped_session(options=options)
    session.begin_nested()  # Savepoint

    old_session = database.session
    database.session = session
    try:
        yield database
    finally:
        session.rollback()
        session.remove()  # Remove session from registry (if using scoped_session)
        transaction.rollback()  # Roll back the outer transaction
        connection.close()  # Close the connection
        database.session = old_session
