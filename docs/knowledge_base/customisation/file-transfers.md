# File Transfers

> InvenioRDM uses pluggable providers for individual record-file lifecycles.

**Prerequisites:** [Service Layer](../architecture/service-layer.md),
[Permissions](permissions.md) **Related:** [Testing](../testing.md)

## Transfer registry

`invenio-records-resources` builds a transfer registry from:

- `RECORDS_RESOURCES_TRANSFERS`: registered provider classes or import strings.
- `RECORDS_RESOURCES_DEFAULT_TRANSFER_TYPE`: the type applied when an upload
    initialization request omits `transfer.type`.

Built-in providers are local (`L`), fetch (`F`), remote (`R`), and multipart (`M`).
Register custom providers before the registry is first accessed.

## Request and persistence model

File initialization accepts a `transfer` object:

```json
{
  "key": "data.csv",
  "transfer": {
    "type": "L"
  }
}
```

`FileService.initial_file_schema` combines the normal file schema with
`InitFileSchemaMixin`. Its dynamic `TransferSchema` selects the registered provider's
`Schema` using `transfer.type`, validating provider-specific transfer metadata.

`FileMetadataComponent.init_files()` resolves the provider and calls
`transfer.init_file(record, file_metadata)`. The base implementation retains the
`transfer` dictionary on the file record; the dynamic schema serializes it in files API
responses.

## Custom providers

Subclass the provider with the closest lifecycle. Local-like providers inherit
`LocalTransfer`; remote and multipart transfers have different requirements.

Every provider sets a unique `transfer_type` and may extend `BaseTransferSchema`:

```python
from marshmallow import fields
from invenio_records_resources.services.files.schema import BaseTransferSchema
from invenio_records_resources.services.files.transfer.providers.local import (
    LocalTransfer,
)


class ExampleTransfer(LocalTransfer):
    transfer_type = "X"

    class Schema(BaseTransferSchema):
        label = fields.Str()
```

The base class implements initialization, stream upload, commit, status, and content
delivery. Override lifecycle methods only when behavior differs.

## Permissions

`IfTransferType` checks the request payload during initialization and the stored file
record later. Extend the RDM policy for applicable create, upload, commit, draft-read,
and published-read operations.

An additional domain permission cannot be expressed by merely adding another generator
to a `can_*_files` list: entries are alternatives. Require the extra policy action
separately from a file-service component, while retaining the normal transfer-type and
record-access checks.

## Rendering and tests

Transfer metadata is available from the files API. The published file list is
Jinja-rendered through `invenio_app_rdm/records/macros/files.html`; use a project
template override for provider-specific values.

Test registration, initialization validation, upload/commit, serialized output,
permissions, and record lifecycle copying through the files REST API.
