# Service Components

> Service components separate independent concerns across service method calls using an
> observer pattern. Each component handles one aspect of record lifecycle (metadata,
> files, access, custom fields, etc.).

**Prerequisites:** [Service Layer](../architecture/service-layer.md) **Related:**
[Permissions](permissions.md), [Custom Fields](custom-fields.md)

## How Components Work

When a service method runs (e.g. `create`), it calls
`self.run_components("create", identity, data=data, record=record, ...)`. This iterates
through every component in the config's `components` list and calls the matching method
on each, in order.

## Writing a Component

Inherit from `ServiceComponent` and override whichever methods you need:

```python
from invenio_records_resources.services.records.components import ServiceComponent

class MyComponent(ServiceComponent):
    def create(self, identity, data=None, record=None, **kwargs):
        """Called during service.create(), after the record object exists."""
        record["my_field"] = data.get("my_field")

    def update_draft(self, identity, data=None, record=None, **kwargs):
        """Called during service.update_draft()."""
        record["my_field"] = data.get("my_field")
```

Always accept `**kwargs` — callers may pass extra keyword arguments.

## Method Reference

| Method                 | Triggered by              | Notes                                         |
| ---------------------- | ------------------------- | --------------------------------------------- |
| `create`               | `service.create()`        | Record object exists but is not yet committed |
| `update_draft`         | `service.update_draft()`  | Full data replacement                         |
| `publish`              | `service.publish()`       | Both `draft` and `record` kwargs available    |
| `edit`                 | `service.edit()`          | Creates edit draft from published record      |
| `new_version`          | `service.new_version()`   | Creates new-version draft                     |
| `delete_draft`         | `service.delete_draft()`  |                                               |
| `delete_record`        | `service.delete_record()` | Soft delete                                   |
| `update_files_options` | `service.update()`        | Files-specific update                         |

## Checking Permissions Inside a Component

Use `self.service.require_permission()` — **not** `flask_principal.Permission`:

```python
from invenio_records_resources.services.errors import PermissionDeniedError

class SubjectFieldComponent(ServiceComponent):
    def _check_subject_permission(self, identity, data):
        subjects = data.get("custom_fields", {}).get("imperial:subjects")
        if subjects:
            # Raises PermissionDeniedError (HTTP 403) if denied.
            # Do NOT use flask_principal.Permission — see Permissions doc.
            self.service.require_permission(identity, "use_subject_field")

    def create(self, identity, data=None, record=None, **kwargs):
        self._check_subject_permission(identity, data)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        self._check_subject_permission(identity, data)
```

`require_permission` raises `PermissionDeniedError` (from
`invenio_records_resources.services.errors`), which the resource layer handles as HTTP
403\. A bare `flask_principal.PermissionDenied` is **not** caught by the resource layer.

Because components run inside the service's Unit of Work, a `PermissionDeniedError`
raised here causes the entire UoW to roll back — no partial record is written to the
database.

## Registering a Component

```python
# invenio.cfg (or settings.py)
from invenio_rdm_records.services.components import DefaultRecordsComponents
from my_site.components import SubjectFieldComponent, AnotherComponent

RDM_RECORDS_SERVICE_COMPONENTS = DefaultRecordsComponents + [
    SubjectFieldComponent,
    AnotherComponent,
]
```

`DefaultRecordsComponents` is a list — appending custom components means they run
**after** the built-in ones (metadata, PID, files, access, etc.).

### Component ordering and prior state

Component order matters. In particular, `MetadataComponent.create()` and
`MetadataComponent.update_draft()` assign the parsed request metadata to the record.
Therefore, a component appended to `DefaultRecordsComponents` sees the new metadata, not
the prior draft metadata.

When a component must compare requested metadata with the existing draft before the
metadata is replaced (for example, to authorize a change to a specific field), insert it
before the default components:

```python
RDM_RECORDS_SERVICE_COMPONENTS = [
    MetadataChangeAuthorizationComponent,
] + DefaultRecordsComponents + [
    SymplecticComponent,
]
```

Keep components that only consume the final record state after
`DefaultRecordsComponents`.

## Accessing Other Services

```python
from invenio_rdm_records.proxies import current_rdm_records_service

class MyComponent(ServiceComponent):
    def publish(self, identity, draft=None, record=None, **kwargs):
        # self.service is the RDM records service
        other_service = current_rdm_records_service.communities
        ...
```
