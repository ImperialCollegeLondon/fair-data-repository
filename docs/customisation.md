We have made a variety of customisations to the base InvenioRDM app. These are potential
pain points, particularly when upgrading to a new version of InvenioRDM. On upgrade all
of the below should be carefully checked to ensure that they are still working as
intended.

## Deposit Permissions

Deposit permissions logic has been updated to provide more granular control over who can
deposit records. The following changes have been made (see [PR #262] and [PR #251]):

- Only users or roles with the `deposit-action` permission can access deposit
    functionality.
- The "New upload" button and related UI elements are shown or hidden based on the
    user's permissions.
- Deposit permission is assigned to users when they login to the system based on their
    identity data according to the check defined in `ext.py`.

### Restricted Licence Permissions

The `restricted-license-action` permission allows a user to choose a licence outside the
public allowlist. It is granted independently of `deposit-action`.

Administrators can grant the permission to a user with:

```console
pipenv run invenio access allow-action-for-user --user EMAIL --action restricted-license-action
```

Revoke it by removing the assignment:

```console
pipenv run invenio access remove-action-from-user --user EMAIL --action restricted-license-action
```

## Deposit Visibility

The deposit metadata schema has been updated to prevent metadata visibility from being
set to `private`. This means that the metadata for all deposits is `public`. The
visibility of files may still be set to `private`.

## Deposit Data Model

The following changes have been made to the schema used to validate and deserialise the
deposit metadata:

- The the `role` subfield of `creators` has been removed. this was considered confusing
    and to provide better alignment with the Datacite metadata schema.
- The `publisher` field has been overridden so that a fixed configurable value is always
    used.
- The `resource_type` field has been overridden so that fixed configurable value is
    always used.
- The `publication_date` field has been overridden so that the date of publication is
    used.
- The `description` field has been made mandatory.
- The `references` field has been overridden to always be empty.
- The `rights` field has been overriden to prevent more that one license from being
    supplied.

## UI Updates

### Layout and Styling

Changes have been made to apply Imperial College London branding to the site. Changes
have been made to style sheets via overrides in the `assets/less/site` directory. HTML
templates have also been overriden in the `templates/semantic-ui` directory. The layout
and styling customisations shoud be carefully rechecked on upgrade (particularly of
`invenio-app-rdm`) to ensure that they are still working as intended.

### Hiding Communities Feature

InvenioRDM provides a feature for creating communities of deposits with an associated
review and approval process for publication. In order to facilitate a central review
process by the library for all deposits we have made use of the in-built communities
feature. Under this model there is a single community to which all deposits are added
and the application UI is updated to remove links and references to communities in key
places.

This has been implemented through the following changes:

- Hiding UI links to pages for creating or listing communities [PR #97].
- Updating links to create a new deposit to have the "icl" community pre-selected.
- Hiding the communities header on the new deposit page.

### Deposit Page

Some changes to the deposit page have made use of the support in InvenioRDM for
overriding React components. See [InvenioRDM Docs: How to override UI React components]
for more details. Overriden components are stored in
`assets/js/invenio_app_rdm/overridableRegistry/mapping.js`. In summary:

- The `creators` field has been customised to remove the `role` subfield. Implemented by
    the custom component `OptionalRoleCreatibutorsField` that allows control over
    whether the role subfield is displayed as well as the display of clarifying help
    text. The implementation of `OptionalRoleCreatibutorsField` unfortunately required
    extensive copy-pasting of the original [CreatibutorsField] component so any updates
    to `invenio-rdm-records` should be carefully checked and any changes manually ported
    over.
- The `contributors` field has been customised to add additional help text. This is also
    implemented using the custom `OptionalRoleCreatibutorsField` component.
- The following fields have been hidden - `resource_type`, `publisher`,
    `publication_date` and `references`. This has been implemented by overriding with
    the custom `HiddenField` component. Some values have still had a default value set
    where we want values to be present in the metadata but not editable by the user.
- The `description` field has been customised to use a standard textarea rather than a
    rich text editor as it was considered that plain text was more appropriate for this
    field. It has also been made a mandatory field.
- The `license` field has been customised to provide a selection of licenses from a
    fixed list. Implemented by the custom component `LimitedLicenseField`. Similar to
    the `OptionalRoleCreatibutorsField` this required extensive copy-pasting of the
    original [LicensesField] component so the same checks and changes should be applied
    on update of `invenio-rdm-records`.
- A checkbox for the data deposit agreement has been added to the modal created by the
    `Submit For Review` button. This checkbox is required to be checked before the user
    can submit their data for review.
- The control for reserving a DOI has been overridden to prevent users from opting out
    of getting a DOI.
- The control for setting metedata visibility has been hidden.
- The `funding` field has been overridden to add additional help text.

Other customisations have used the [APP_RDM_DEPOSIT_FORM_DEFAULTS] setting (set in
`site/ic_data_repo/config/settings.py`). In summary:

- `resource_type` has been set to "dataset".
- `publication_data` is set to the current date.
- `rights` is set to the CC-BY-4.0 license.
- `publisher` is set to "Imperial College London".
- `creators` is set to the logged in user.

## Settings Menu Customisation

The "Applications" settings menu item in the UI has been hidden to prevent confusion and
streamline the user experience. This was implemented in [PR #270].

## Authentication

Authentication via Imperial SSO is handled by the `ic_data_repo.auth.oauth` module. This
implements an `info_handler` function that extracts user information the SSO response.
Relevant settings for are set in `ic_data_repo.config.settings`.

## Symplectic Integration

An integration with Symplectic Elements API has been implemented. This comprises:

- Creation and synchronisation of a deposit with a record in Symplectic elements.
- A relationship is created in Symplectic between the deposit Symplectic record and any
    existing publication Symplectic records with a DOI that has been included as a
    related identifier in the deposit metadata.
- A relationship is created in Symplectic between the deposit Symplectic record and any
    existing Symplectic awards with an internal or funder reference provided as funding
    item in the deposit metadata.

## Domain Metadata

Records can be tagged with domain-specific classification terms via the
`imperial:domain_metadata` custom field: a multi-value list of `{id, value}`
pairs. `id` must reference a term in a dedicated `domainmetadatascheme`
vocabulary.

`value` is required, free-text subject content supplied by the client,
independent of the referenced term.

Records only ever persist exactly `{id, value}` - nothing from the
vocabulary term (title, or any other property) is copied onto the stored
record.

`id` must be unique across this ENTIRE vocabulary, not just within one
external scheme - it's a single flat namespace, not partitioned per 
scheme. If terms are drawn from more than one external classification
system, prefix each id with a short scheme identifier to avoid two
unrelated schemes' native codes colliding, e.g.:
   mesh-<mesh-code>
   anzsrc-<anzsrc-code>

### Fixtures

Terms are defined in `app_data/vocabularies/domain_metadata_schemes.yaml`
(mirrored for tests in `tests/data/vocabularies/`), using InvenioRDM's
standard generic-vocabulary fixture format - just `id` and a localized
`title` are needed; nothing about a term's own properties is read by the
custom field.

### Initial loading and live updates

The vocabulary is loaded the same way as any other InvenioRDM vocabulary:

- On first setup, `invenio rdm-records fixtures` loads it along with
    everything else - this only runs once; it skips vocabularies that have
    already been loaded.
- To add or update terms later, edit the YAML file and run:

    ```console
    pipenv run invenio rdm-records add-to-fixture domainmetadatascheme
    ```

    This upserts by `id` - existing terms are updated in place and new ones
    created, so terms can be revised and re-applied without downtime.

### OpenSearch mapping initialization

Adding a new custom field to an instance whose search index already exists
requires explicitly pushing its mapping - InvenioRDM does not do this
automatically from a config change alone:

```console
pipenv run invenio custom-fields init -f imperial:domain_metadata
```

Omit `-f imperial:domain_metadata` to (re-)create the mappings for every
configured custom field instead of just this one. This only needs to run
once per environment, when the field is first deployed to it (or after
changing its `mapping`) - `invenio rdm-records fixtures`, used for vocabulary
data, does not touch custom field mappings at all.

[app_rdm_deposit_form_defaults]: https://github.com/inveniosoftware/invenio-app-rdm/blob/af193c7a5fcb728343c7898ac4f52a5a5b44c95a/invenio_app_rdm/config.py#L917-L940
[creatibutorsfield]: https://github.com/inveniosoftware/invenio-rdm-records/blob/v10.9.1/invenio_rdm_records/assets/semantic-ui/js/invenio_rdm_records/src/deposit/fields/CreatibutorsField/CreatibutorsField.js
[inveniordm docs: how to override ui react components]: https://inveniordm.docs.cern.ch/develop/howtos/override_components/
[licensesfield]: https://github.com/inveniosoftware/invenio-rdm-records/blob/v10.9.1/invenio_rdm_records/assets/semantic-ui/js/invenio_rdm_records/src/deposit/fields/License/LicenseField.js
[pr #251]: https://github.com/ImperialCollegeLondon/fair-data-repository/pull/251
[pr #262]: https://github.com/ImperialCollegeLondon/fair-data-repository/pull/262
[pr #270]: https://github.com/ImperialCollegeLondon/fair-data-repository/pull/270
[pr #97]: https://github.com/ImperialCollegeLondon/fair-data-repository/pull/97/files
