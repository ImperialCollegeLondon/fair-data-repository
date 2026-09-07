# Testing

> Patterns and gotchas for writing tests against the InvenioRDM service and API layers
> in this project.

**Related:** [Service Layer](architecture/service-layer.md),
[Permissions](customisation/permissions.md),
[Service Workflows](customisation/service-workflows.md)

## Test Layout

```
tests/
  conftest.py              # module-scoped app, db, and search fixtures
  test_*.py                # unit/service-layer tests (no HTTP)
  api/
    conftest.py            # create_api app, token/user fixtures
    test_*.py              # REST API integration tests
```

API tests use `create_api` (from `invenio_app.factory`) — there is no `/api` prefix on
routes. The unit tests use `create_app` (the full UI+API app).

## Database Session Behaviour

The `db` fixture uses `PytestInvenioSession`, which overrides `commit()` → `flush()`.
This keeps all test state inside an outer transaction that is rolled back after each
test, preventing cross-test pollution.

**Consequence:** `UnitOfWork.rollback()` calls `session.rollback()`, which in the test
session rolls back **all the way to the outer test savepoint** — not just to the UoW's
inner savepoint. This means that after a service call fails inside a UoW (e.g.
`PermissionDeniedError`), any DB rows added during fixture setup (OAuth tokens,
`ActionUsers` grants) may be lost if they were flushed but not committed within the same
nested savepoint.

For rollback assertions, query the DB directly rather than making a second authenticated
HTTP request:

```python
from invenio_rdm_records.records.models import RDMDraftMetadata

# ✅ Safe — ORM query survives session rollback
assert db.session.query(RDMDraftMetadata).count() == 0

# ❌ Fragile — the token may have been wiped by the rollback
response = client.get("/user/records", headers=api_headers)
```

## Granting Action Permissions to Users

```python
from invenio_access.permissions import ActionUsers
from my_site.permissions import deposit_action, subject_metadata_action


@pytest.fixture
def user_subject_depositor(user, db):
    db.session.add(ActionUsers.allow(deposit_action, user_id=user.id))
    db.session.add(ActionUsers.allow(subject_metadata_action, user_id=user.id))
    return user
```

## Creating API Tokens for Tests

```python
from invenio_oauth2server.models import Token
from invenio_oauth2server.proxies import current_oauth2server


@pytest.fixture
def api_headers(db, user_depositor):
    scopes = [s[0] for s in current_oauth2server.scope_choices()]
    token = Token.create_personal("test_token", user_depositor.id, scopes=scopes)
    db.session.commit()
    return {
        "Authorization": f"Bearer {token.access_token}",
        "Content-Type": "application/json",
    }
```

## Overriding App Config per Module

The `app_config` fixture is module-scoped. Override it in your module's `conftest.py` by
requesting the parent `app_config` and mutating the dict:

```python
# tests/api/conftest.py
@pytest.fixture(scope="module")
def app_config(app_config):
    app_config["RDM_COMMUNITY_REQUIRED_TO_PUBLISH"] = False
    return app_config
```

The root `tests/conftest.py` merges `settings.__dict__` over the base config, so
production defaults are active unless you explicitly override them.

## Minimum Required Fields for Publishing

A draft can be created with only `title` and `creators`, but publishing requires
additional fields that are validated at publish time:

```python
{
    "metadata": {
        "title": "...",
        "description": "...",  # required to publish
        "resource_type": {"id": "dataset"},  # required to publish
        "publication_date": "2024-01-01",  # required to publish
        "creators": [...],
    },
    "files": {"enabled": False},
}
```

## Useful Model Classes for DB Assertions

| Model               | Import                               | Use                             |
| ------------------- | ------------------------------------ | ------------------------------- |
| `RDMDraftMetadata`  | `invenio_rdm_records.records.models` | Assert drafts exist/don't exist |
| `RDMRecordMetadata` | `invenio_rdm_records.records.models` | Assert published records        |
| `ActionUsers`       | `invenio_access.permissions`         | Grant/query action permissions  |
| `Token`             | `invenio_oauth2server.models`        | Create personal API tokens      |

Note: `RDMDraft` and `RDMRecord` are Record API classes, **not** SQLAlchemy models —
they do not have a `.query` attribute. Use the `*Metadata` models for direct DB queries.

## Redis Identity Caching

InvenioRDM caches identity needs in Redis after first load. If tests share the same user
across test functions, a stale cached identity may not reflect new `ActionUsers` grants.
The `flush_redis` fixture (available in `tests/conftest.py`) clears Redis between tests
to prevent this.
