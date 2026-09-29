# Custom Fields

> Custom fields extend the record/community metadata schema with additional
> domain-specific fields, configurable entirely via `invenio.cfg`.

**Prerequisites:** [Architecture Overview](../architecture/overview.md),
[Service Layer](../architecture/service-layer.md) **Related:**
[Permissions](permissions.md), [Search and Mappings](search-and-mappings.md)

## Overview

Custom fields allow you to add extra metadata to records (or communities) without
modifying InvenioRDM source code. They involve three configuration layers:

1. **Backend** — field type, validation, and search indexing (`RDM_CUSTOM_FIELDS`)
1. **Namespacing** — avoid name clashes (`RDM_NAMESPACES`)
1. **UI** — display in deposit form and landing page (`RDM_CUSTOM_FIELDS_UI`)

## Configuration

### 1. Namespaces

```python
# invenio.cfg
RDM_NAMESPACES = {
    "cern": "https://greybook.cern.ch/",
    "imperial": "https://www.imperial.ac.uk/",
}
```

Field names are prefixed with the namespace key (e.g. `imperial:project_code`).

### 2. Field Definitions

```python
from invenio_records_resources.services.custom_fields import TextCF, KeywordCF
from invenio_vocabularies.services.custom_fields import VocabularyCF

RDM_CUSTOM_FIELDS = [
    VocabularyCF(
        name="cern:experiment",
        vocabulary_id="cernexperiments",
        dump_options=True,   # all values shown in dropdown
        multiple=False,
    ),
    TextCF(
        name="cern:description",
        field_cls=SanitizedHTML,  # optional: override marshmallow field
    ),
    KeywordCF(name="imperial:project_code"),
]
```

### 3. UI Configuration

```python
RDM_CUSTOM_FIELDS_UI = [
    {
        "section": "CERN Experiment",
        "hide_from_landing_page": False,
        "hide_from_upload_form": False,
        "fields": [
            dict(
                field="cern:experiment",
                ui_widget="Dropdown",
                props=dict(
                    label="Experiment",
                    placeholder="Select...",
                    description="The CERN experiment.",
                    search=False,
                    multiple=False,
                    clearable=True,
                )
            ),
        ]
    }
]
```

## Field Types Reference

| Type               | Use case                   | Search behaviour                                        |
| ------------------ | -------------------------- | ------------------------------------------------------- |
| `TextCF`           | Free text (searchable)     | Full-text search; add `use_as_filter=True` for faceting |
| `KeywordCF`        | Short exact-match text     | Exact match only (good for facets)                      |
| `VocabularyCF`     | Controlled vocabulary term | Keyword on `.id` subfield                               |
| `ISODateStringCF`  | Dates (`YYYY-MM-DD`)       | Date range queries                                      |
| `EDTFDateStringCF` | Extended date/time format  | Date range queries                                      |
| `BooleanCF`        | True/False                 | Boolean filter                                          |
| `IntegerCF`        | Integers                   | Numeric range                                           |
| `DoubleCF`         | Floating point             | Numeric range                                           |

## UI Widgets Reference

| Widget                 | Use with                          | Notes                      |
| ---------------------- | --------------------------------- | -------------------------- |
| `Input`                | TextCF, KeywordCF                 | Single-line text input     |
| `MultiInput`           | TextCF (multiple)                 | Multi-value, like subjects |
| `TextArea`             | TextCF                            | Long text                  |
| `RichInput`            | TextCF + SanitizedHTML            | WYSIWYG editor             |
| `Dropdown`             | VocabularyCF (dump_options=True)  | Shows all options          |
| `AutocompleteDropdown` | VocabularyCF (dump_options=False) | Search-as-you-type         |

## Initialisation

After adding/changing custom fields, run:

```bash
# Initialize all custom fields (creates search mappings)
invenio rdm-records custom-fields init

# Or specific fields only
invenio rdm-records custom-fields init -f cern:experiment
```

This is automatic on first `invenio-cli services setup`.

## Adding as Search Facets

```python
from invenio_rdm_records.config import RDM_FACETS, RDM_SEARCH
from invenio_records_resources.services.records.facets import CFTermsFacet

RDM_FACETS = {
    **RDM_FACETS,
    "experiment": {
        "facet": CFTermsFacet(
            field="cern:experiment.id",      # .id for vocab, plain for keyword
            label="CERN Experiment",
        ),
        "ui": {
            "field": CFTermsFacet.field("cern:experiment.id"),
        },
    },
}

RDM_SEARCH = {
    **RDM_SEARCH,
    "facets": RDM_SEARCH["facets"] + ["experiment"]
}
```

For `TextCF` with `use_as_filter=True`, use `field="name.keyword"` in the facet.

## Custom Validation

```python
from marshmallow import validate

RDM_CUSTOM_FIELDS = [
    TextCF(
        name="cern:url",
        field_args={
            "validate": validate.URL(),
            "required": True,
            "error_messages": {
                "required": "Experiment URL is required."
            }
        },
    ),
]
```

## Landing Page Templates

Override rendering for a specific field:

```python
dict(
    field="my:field",
    ui_widget="Input",
    template="/my_custom_template.html",  # in templates/ dir
    props=dict(...)
)
```

Template receives `field_value` and `field_cfg` variables.

## Communities Custom Fields

Same pattern but using different config variables:

```python
COMMUNITIES_NAMESPACES = { ... }
COMMUNITIES_CUSTOM_FIELDS = [ ... ]
COMMUNITIES_CUSTOM_FIELDS_UI = [ ... ]
```

## Key Implementation Details

- Custom fields are stored in the record JSON under the `custom_fields` top-level key
- They are indexed in OpenSearch under `custom_fields.*`
- The `CustomFieldsComponent` service component handles reading/writing them
- Field types map to OpenSearch mapping types automatically on `init`
- Validation happens at the marshmallow schema level during service calls
