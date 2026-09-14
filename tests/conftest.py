"""Global test fixtures."""

import json
import os
from pathlib import Path

import pytest
import redis
from invenio_access.permissions import system_identity
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


@pytest.fixture(scope="session")
def rabbitmq_container():
    """Start a RabbitMQ container."""
    from testcontainers.rabbitmq import RabbitMqContainer

    with RabbitMqContainer() as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(5672)

        yield {"host": host, "port": port}


@pytest.fixture(scope="module")
def app_config(opensearch_container, redis_container, rabbitmq_container, app_config):
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

    # RabbitMQ config.
    rabbitmq_host = rabbitmq_container["host"]
    rabbitmq_port = rabbitmq_container["port"]
    app_config["BROKER_URL"] = f"amqp://guest:guest@{rabbitmq_host}:{rabbitmq_port}/"
    app_config["CELERY_BROKER_URL"] = (
        f"amqp://guest:guest@{rabbitmq_host}:{rabbitmq_port}/"
    )

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

    return (
        settings.__dict__
        | app_config
        | {
            "SYMPLECTIC_API_URL": "",
            "SYMPLECTIC_API_SUBSCRIPTION_KEY": "",
            "SYMLECTIC_ENABLED": True,
        }
    )


@pytest.fixture(scope="module")
def create_app():
    """Provide the Flask app object used by tests."""
    from invenio_app.factory import (
        app_class,
        config_loader,
        create_app_factory,
        create_wsgi_factory,
        instance_path,
        static_folder,
        static_url_path,
    )
    from invenio_base.urls import create_invenio_apps_urls_builder_factory
    from invenio_base.wsgi import wsgi_proxyfix

    # The following code is boilerplate copied from:
    # https://github.com/inveniosoftware/invenio-app/blob/fcde4f4936d6e26338faf9cab81207b79843d2f5/invenio_app/factory.py#L87
    # The purpose of reproducing it here is so that a new app factory is created in the
    # pytest module scope. The root cause for needing this rather than just directly
    # using invenio_app.factory.create_app comes from:
    # https://github.com/inveniosoftware/invenio-base/blob/404908d766249d5114ccf465c0dfef00b484a3b2/invenio_base/app.py#L104-L106
    # The update to app_kwargs subtly makes the returned factory no longer idempotent.
    # The first time the factory is called the callables in app_kwargs are evaluated and
    # the results are stored in the app_kwargs dict. This includes temporary directory
    # paths that are linked to the pytest module scope. On subsequent calls to the
    # factory in another test module, the callables are not evaluated again and the
    # previous temporary directory paths are no longer valid. This causes subtle issues
    # with the resultant app e.g. the paths passed to the Jinja2 template loader are no
    # longer valid and Helix template overrides are not applied.

    # This may need revision on Invenio upgrade.

    create_api = create_app_factory(
        "invenio",
        config_loader=config_loader,
        blueprint_entry_points=["invenio_base.api_blueprints"],
        extension_entry_points=["invenio_base.api_apps"],
        converter_entry_points=["invenio_base.api_converters"],
        finalize_app_entry_points=["invenio_base.api_finalize_app"],
        wsgi_factory=wsgi_proxyfix(),
        instance_path=instance_path,
        root_path=instance_path,
        app_class=app_class(),
        urls_builder_factory=create_invenio_apps_urls_builder_factory(
            "SITE_API_URL",
            "SITE_UI_URL",
            {
                "blueprints": ["invenio_base.blueprints"],
                "converters": ["invenio_base.converters"],
            },
        ),
    )
    return create_app_factory(
        "invenio",
        config_loader=config_loader,
        blueprint_entry_points=["invenio_base.blueprints"],
        extension_entry_points=["invenio_base.apps"],
        converter_entry_points=["invenio_base.converters"],
        finalize_app_entry_points=["invenio_base.finalize_app"],
        wsgi_factory=wsgi_proxyfix(create_wsgi_factory({"/api": create_api})),
        instance_path=instance_path,
        static_folder=static_folder,
        root_path=instance_path,
        static_url_path=static_url_path(),
        app_class=app_class(),
        urls_builder_factory=create_invenio_apps_urls_builder_factory(
            "SITE_UI_URL",
            "SITE_API_URL",
            {
                "blueprints": ["invenio_base.api_blueprints"],
                "converters": ["invenio_base.api_converters"],
            },
        ),
    )


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
def db(db):
    """Test scoped database fixture.

    Extends the implementation from pytest_invenio to ensure that a transaction is
    started for sqlite databases. This makes sure that each test has a dedicated
    transaction that is rolled back at the end to provide test isolation. Sqlite by
    default defers transaction creation which can cause issues with rollbacks.
    """
    connection = db.session.get_bind()
    if connection.dialect.name == "sqlite":
        connection.exec_driver_sql("BEGIN")
    return db
