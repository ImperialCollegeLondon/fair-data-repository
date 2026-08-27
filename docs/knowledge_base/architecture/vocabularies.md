# Vocabularies

> InvenioRDM vocabularies are controlled records used by metadata fields, loaded as
> fixtures and searchable through dedicated services and REST endpoints.

**Prerequisites:** [Service Layer](service-layer.md) **Related:**
[Services Catalogue](services-catalogue.md),
[Project Customisations](../../customisation.md#vocabularies)

## What vocabularies provide

Vocabulary records supply stable identifiers and display metadata for controlled values
such as licenses, languages, resource types, subjects, affiliations, funders, names, and
awards. Record metadata normally stores a vocabulary relation by ID; the service
resolves and serializes the corresponding title, description, tags, and properties.

The `invenio-vocabularies` services persist and index terms. Standard vocabulary types
are searched through `GET /api/vocabularies/<type>`; the endpoint supports `q`,
`suggest`, `tags`, sorting, and pagination. Larger domain-specific vocabularies use
their own API endpoints.

## Fixture layout and precedence

InvenioRDM reads `app_data/vocabularies.yaml` first. It declares a vocabulary's
identifier, PID type, and data file; scheme-based vocabularies such as `subjects` can
declare multiple scheme files. If a local fixture is absent, InvenioRDM falls back to
extension-provided data and then the upstream default fixture.

```text
app_data/
  vocabularies.yaml
  vocabularies/
    licenses.csv
    subjects_oecd_fos.yaml
```

The entry format depends on the vocabulary type. YAML records commonly contain `id`,
localized `title`, and vocabulary-specific `props`; the license fixture in this project
is CSV. Consult the matching upstream default fixture before adding a new type or field.

## Initial loading

Prepare `app_data/` before initial setup. `invenio-cli services setup` queues fixture
loading; Celery workers create the vocabulary records and search documents. Running
`invenio-cli run` locally processes queued work.

For local development only, `invenio-cli services setup --force` wipes the database and
indices before reloading fixtures. Never use `--force` against a production instance.

## Updating a live instance

Fixture loading is additive: `uv run invenio rdm-records fixtures` can add entries that
do not yet exist, but does not overwrite existing records. For supported additions and
updates, use:

```bash
uv run invenio rdm-records add-to-fixture <vocabulary_name>
```

This command adds new entries or updates existing entries, but does not delete existing
entries. Treat deletions and identifier changes as a separate migration problem because
existing records may refer to those IDs.

## References

- [InvenioRDM: Customize vocabularies](https://inveniordm.docs.cern.ch/operate/customize/vocabularies/)
- [InvenioRDM: Vocabularies REST API](https://inveniordm.docs.cern.ch/reference/rest_api_vocabularies/)
- Project fixture declaration: `app_data/vocabularies.yaml`
- [Upstream default fixtures](https://github.com/inveniosoftware/invenio-rdm-records/tree/master/invenio_rdm_records/fixtures/data)
