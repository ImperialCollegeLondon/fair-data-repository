# Service Layer

> The service layer contains business logic, authorization, and control flow. It is
> interface-independent and can be called from REST APIs, CLI, or Celery tasks.

**Prerequisites:** [Architecture Overview](overview.md) **Related:**
[Services Catalogue](services-catalogue.md), [Data Access Layer](data-access-layer.md),
[Service Components](../customisation/service-components.md),
[Permissions](../customisation/permissions.md)

## Core Concepts

### Service Class

A service provides methods that map directly to user actions (create, read, update,
delete, search, etc.):

```python
from invenio_records_resources.services import Service


class MyService(Service):
    def create(self, identity, data, uow=None):
        self.require_permission(identity, "create")
        # ... business logic ...
        return self.result_item(self, identity, record)
```

### Service Config (Dependency Injection)

All customisable dependencies are injected via a config object:

```python
from invenio_records_resources.services import ServiceConfig


class MyServiceConfig(ServiceConfig):
    permission_policy_cls = MyPermissionPolicy
    schema = MySchema
    components = [MetadataComponent, PIDComponent]
    result_item_cls = MyResultItem
```

The config is built with the app context: `MyServiceConfig.build(app)`.

### Identity

Every service method receives an `identity` parameter — never accesses Flask's request
context directly. In REST endpoints: `g.identity`. For system operations:
`system_identity` from `invenio_access.permissions`.

## Unit of Work (UoW)

State-changing methods must use the UoW pattern to ensure atomicity:

```python
from invenio_records_resources.services.uow import unit_of_work, RecordCommitOp


class MyService(Service):
    @unit_of_work()
    def create(self, identity, data, uow=None):
        record = self.record_cls.create(data)
        uow.register(RecordCommitOp(record, indexer=self.indexer))
        return self.result_item(self, identity, record)
```

**Rules:**

- Never call `db.session.commit()` directly in a service method.
- The `@unit_of_work()` decorator auto-creates a UoW if none is passed.
- Multiple service calls can share one UoW for transactional grouping.
- UoW ensures: DB commit → then index → then Celery tasks (in that order).

## Service Components

Components separate independent concerns across service methods using an observer
pattern:

```python
from invenio_records_resources.services.records.components import ServiceComponent


class MetadataComponent(ServiceComponent):
    def create(self, identity, data=None, record=None, **kwargs):
        record.metadata = data.get("metadata", {})

    def update(self, identity, data=None, record=None, **kwargs):
        record.metadata = data.get("metadata", {})
```

Components are registered in the config's `components` list and executed in order via
`self.run_components('method_name', ...)`.

## Permissions

Checked via `self.require_permission(identity, action_name, **kwargs)`:

```python
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, SystemProcess


class MyPermissionPolicy(RecordPermissionPolicy):
    can_create = [AnyUser(), SystemProcess()]
    can_read = [AnyUser()]
    can_update = [RecordOwners()]
    can_delete = [SystemProcess()]
```

Each `can_<action>` is a list of "need generators" that produce permission needs. If any
generator grants access, the action is allowed.

## Service Schema (Marshmallow)

Responsible for:

- Deserializing and validating input data
- Field-level permission checks (hiding fields from certain users)
- Serializing record projections for output

## Service Results

Services never return raw data-layer objects. They wrap them in result items that
provide identity-scoped views:

```python
result = service.read(identity, id_)
result.to_dict()  # serialized, permission-filtered view
```

## Error Handling

Services raise domain-specific exceptions — never `HTTPException` or `abort()`:

```python
class RecordNotFoundError(ServiceException):
    pass
```

The presentation layer maps these to HTTP status codes.

## Bootstrapping (ext.py)

Services are instantiated in the Flask extension and accessed via proxies:

```python
# ext.py
class MyExtension:
    def init_services(self, app):
        self.service = MyService(MyServiceConfig.build(app))


# proxies.py
current_service = LocalProxy(lambda: current_app.extensions["myext"].service)
```
