# Upgrading to InvenioRDM v14

Helix moved from InvenioRDM v13 to v14 and from Python 3.12 to Python 3.14. This page
covers what contributors need to do to their local environment and the one-off migration
that must be run against each deployed instance (dev and prod).

It is based on the upstream [v14 upgrade guide]; refer to that for background on each
step.

## Summary of changes

- Python 3.14 is required (`requires-python = "~=3.14.0"`).
- `invenio-app-rdm[opensearch2]~=14.0.0`.
- The frontend is now built with Rspack, which needs Node.js 20.19+ or 22.12+. We use
    Node 22.
- The Docker image installs a uv-managed Python 3.14 into `/opt/python` as AlmaLinux
    only ships Python 3.12.
- The database schema, search indices and some vocabularies change and must be migrated
    (see below).

## Upgrading your local development environment

### 1. Update your tools

- **uv**: a recent version is needed to download Python 3.14. Older versions fail with
    `No download found for request: cpython-3.14-...`. Update with `uv self update`, or
    if uv was installed some other way (e.g. pip) re-run the
    [uv installation instructions]. Check with `uv --version`.

- **invenio-cli**: v1.12.0 or newer is required:

    ```console
    uv tool install --force "invenio-cli>=1.12"
    invenio-cli --version
    ```

- **Node.js**: install and select Node 22, e.g. with [nvm]:

    ```console
    nvm install 22
    nvm use 22
    nvm alias default 22
    ```

    With Node 18 the asset build fails with
    `Unsupported Node.js version ... Rspack requires Node.js 20.19+ or 22.12+`.

- **pnpm**: unchanged (v11).

### 2. (Optional) Prepare your existing database

If you want to keep your existing local data, run this **before** switching to the v14
code, while your environment is still on v13. InvenioRDM v13 could fail to create the
`alembic_version` table, which the v14 schema migration relies on. The script records
the current (v13) schema revision, so it must be run with v13 installed.

```console
curl -fsSLO https://raw.githubusercontent.com/inveniosoftware/docs-invenio-rdm/master/docs/releases/v14/ensure_alembic_version_table_exists.py
invenio-cli services start
uv run invenio shell ensure_alembic_version_table_exists.py
```

If you're happy to start again from an empty instance, skip this step.

### 3. Rebuild the virtual environment

Switch to the v14 code and recreate the virtual environment from scratch:

```console
git switch <v14 branch>
rm -rf .venv
invenio-cli install
```

uv will download Python 3.14 if it isn't already available. Afterwards:

- `uv run python --version` should report Python 3.14.
- Re-run `uv run pre-commit install` if you use pre-commit from the dev dependencies.
- Point your IDE at the new `.venv` interpreter.

### 4. Migrate or recreate your local data

Either start from scratch:

```console
invenio-cli services destroy
invenio-cli services setup --no-demo-data
```

then recreate your users, the `icl` community and permissions as described in
[Local Installation](index.md#local-installation).

Or, if you ran step 2, migrate your existing data by following the
[migration steps](#migration-steps) below, prefixing each `invenio` command with
`uv run` and running `invenio-cli run` (for the Celery workers) where the steps say the
workers must be running.

## Migrating a deployed instance (Kubernetes)

The dev and prod instances run on AKS using the image built from this repository and the
[ImperialCollegeLondon/helm-invenio] chart. Merging to `develop` deploys to dev and
merging to `main` deploys to prod (see `.github/workflows/publish.yml` and
`deploy.yml`). The chart runs the `web`, `worker` and `worker-beat` Deployments in the
`invenio` namespace.

!!! warning

    Deploying the v14 image is not enough on its own. Until the migration below has been
    completed the site will be broken, so schedule a maintenance window and let users know.
    **Always rehearse on dev (merge to `develop`) before prod.**

The steps below assume you have `kubectl` access to the cluster (see
`README-Imperial.md` in the Helm chart repository). For brevity:

```console
alias k="kubectl -n invenio"
```

### Before deploying (still on v13)

1. **Record the current image** so you can roll back:

    ```console
    k get deploy web -o jsonpath='{.spec.template.spec.containers[0].image}'
    ```

1. **Back up** the PostgreSQL database (external to the cluster, e.g. an on-demand
    backup or `pg_dump`) and take an OpenSearch snapshot. The statistics indices cannot
    be rebuilt from the database. The migration does not modify uploaded files, but
    snapshotting the files share is recommended too.

1. **Ensure the `alembic_version` table exists.** This must run against the **v13**
    image. Download the script locally and stream it into the running web pod:

    ```console
    curl -fsSLO https://raw.githubusercontent.com/inveniosoftware/docs-invenio-rdm/master/docs/releases/v14/ensure_alembic_version_table_exists.py
    k exec -i deploy/web -- sh -c 'cat > /tmp/ensure_alembic_version_table_exists.py' < ensure_alembic_version_table_exists.py
    k exec deploy/web -- invenio shell /tmp/ensure_alembic_version_table_exists.py
    ```

    It should print "Everything is fine, ...".

### Deploy and migrate

1. **Deploy the v14 image** by merging to the relevant branch. Wait for the rollout to
    finish:

    ```console
    k rollout status deploy/web
    k rollout status deploy/worker
    k rollout status deploy/worker-beat
    ```

1. **Stop the Celery workers** so nothing touches the database mid-migration. Note the
    current replica count of `worker` first, so you can restore it:

    ```console
    k get deploy worker -o jsonpath='{.spec.replicas}'
    k scale deploy worker worker-beat --replicas=0
    ```

1. **Open a shell in a web pod** (the remaining commands run inside it):

    ```console
    k exec -it deploy/web -- bash
    ```

1. Follow the [migration steps](#migration-steps) below, scaling the workers back up
    (from your local terminal) where indicated:

    ```console
    k scale deploy worker --replicas=<previous count>
    k scale deploy worker-beat --replicas=1
    ```

    A subsequent deploy will also reset the replica counts to the values in the chart.

1. **Check the site**: search returns all records, records and communities display, the
    deposit form at `/uploads/new` loads, OAI-PMH responds and usage statistics are
    still present.

### Rolling back

Restore the database backup and OpenSearch snapshot, then redeploy the previous image by
running the "Deploy to AKS" workflow manually (`workflow_dispatch`) with the digest
recorded above.

## Migration steps

These are the same for local and deployed instances. Locally, prefix `invenio` and
`python` with `uv run`.

1. **Locate the upgrade scripts** shipped with `invenio-app-rdm`:

    ```console
    SCRIPTS=$(python -c 'import invenio_app_rdm, pathlib; print(pathlib.Path(invenio_app_rdm.__file__).parent / "upgrade_scripts")')
    ls $SCRIPTS
    ```

1. **Migrate the database** (workers stopped):

    ```console
    invenio shell $SCRIPTS/prepare_migration_13_0_to_14_0.py
    invenio alembic upgrade
    invenio shell $SCRIPTS/migrate_13_0_to_14_0.py
    ```

    The prepare script drops the `invenio-github` tables (we don't use that package) and
    should finish with "v13 -> v14 database cleanup completed successfully". The final
    script reports "No data migration for v14".

    If `invenio alembic upgrade` fails with a unique constraint violation, see the
    troubleshooting section of the [v14 upgrade guide]. This is caused by leftover rows
    that need deleting by hand.

1. **Recreate the search indices.** This only deletes the indices defined by mappings
    (records, communities, users, vocabularies etc.). The statistics indices
    (`*-events-stats-*`, `*-stats-*`) are left untouched, so view and download counts
    are preserved. This was verified on a local instance. Before you start, run
    `curl -s '<opensearch>/_cat/indices?v'` and keep the output, so you can compare the
    document counts afterwards.

    ```console
    invenio index destroy --yes-i-know
    invenio index init
    invenio rdm-records custom-fields init
    ```

1. **Start the Celery workers again.** Reindexing and vocabulary loading are queued as
    Celery tasks, so the workers must be running from here on (locally, start
    `invenio-cli run`).

1. **Rebuild the indices.** Search results will be incomplete until the workers have
    worked through the queue.

    ```console
    invenio rdm rebuild-all-indices
    ```

1. **Update the OAI-PMH percolator and job logs datastream.** Download
    `migrate_percolator_and_jobs_datastream.py` from the same location as
    `ensure_alembic_version_table_exists.py` above (for a deployed instance, stream it
    into the pod the same way, to `/tmp`) and run it:

    ```console
    invenio shell /tmp/migrate_percolator_and_jobs_datastream.py
    ```

    Locally, pass the path you downloaded it to instead.

1. **Update the vocabularies** changed by the DataCite 4.4–4.7 alignment. These only add
    new entries. Where we override a vocabulary in `app_data/vocabularies.yaml`
    (licenses and resource types) our own file is used, so those are effectively
    no-ops.

    ```console
    invenio rdm-records add-to-fixture datetypes
    invenio rdm-records add-to-fixture descriptiontypes
    invenio rdm-records add-to-fixture licenses
    invenio rdm-records add-to-fixture relationtypes
    invenio rdm-records add-to-fixture resourcetypes
    invenio rdm-records add-to-fixture contributorsroles
    invenio rdm-records add-to-fixture creatorsroles
    invenio rdm-records add-to-fixture titletypes
    invenio rdm-records add-to-fixture removalreasons
    ```

    `removalreasons` is required: the v14 deposit form fails to load (with a 404) without
    it.

### Steps from the upstream guide that don't apply

- **Resource type alignment** (Thesis/Dissertation): Helix only supports datasets.
- **Role ID migration** (`migrate_role_ids_to_names.py`): only needed if custom code
    relies on `RoleNeed` values, which ours doesn't. Run it if role-based permissions
    misbehave after the upgrade.
- **`SITE_UI_URL`/`SITE_API_URL`**: already set explicitly in our config modules.

[imperialcollegelondon/helm-invenio]: https://github.com/ImperialCollegeLondon/helm-invenio
[nvm]: https://github.com/nvm-sh/nvm
[uv installation instructions]: https://docs.astral.sh/uv/getting-started/installation/
[v14 upgrade guide]: https://inveniordm.docs.cern.ch/releases/v14/upgrade-v14.0/
