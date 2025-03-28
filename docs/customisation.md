We have made a variety of customisations to the base InvenioRDM app. These are potential
pain points, particularly when upgrading to a new version of InvenioRDM. On upgrade all
of the below should be carefully checked to ensure that they are still working as
intended.

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

This has been done by the following changes:

- Hiding UI links to pages for creating or listing communities [PR #97].
- Updating links to create a new deposit to have the "icl" community pre-selected.
- Hiding the communities header on the new deposit page.

### Deposit Form

Some changes to the deposit form have made use of the support in InvenioRDM for
overriding React components. See [InvenioRDM Docs: How to override UI React components]
for more details. Overriden components are stored in
`assets/js/invenio_app_rdm/overridableRegistry/mapping.js`. In summary:

- The `creators` field has been customised to remove the `role` subfield as this was
    considered confusing and to provide better alignment with the Datacite metadata
    schema. Implemented by the custom component `OptionalRoleCreatibutorsField` that
    allows control over whether the role subfield is displayed as well as the display of
    clarifying help text. The implementation of `OptionalRoleCreatibutorsField`
    unfortunately required extensive copy-pasting of the original [CreatibutorsField]
    component so any updates to `invenio-rdm-records` should be carefully checked and
    any changes manually ported over.
- The `contributors` field has been customised to add additional help text. This is also
    implemented using the custom `OptionalRoleCreatibutorsField` component.
- The following fields have been hidden - `resource_type`, `publisher`,
    `publication_date` and `references`. This has been implemented by overriding with
    the custom `HiddenField` component. Some values have still had a default value set
    where we want values to be present in the metadata but not editable by the user.
- The `description` field has been customised to use a standard textarea rather than a
    rich text editor as it was considered that plain text was more appropriate for this
    field.
- The `license` field has been customised to provide a selection of licenses from a
    fixed list. Implemented by the custom component `LimitedLicenseField`. Similar to
    the `OptionalRoleCreatibutorsField` this required extensive copy-pasting of the
    original [LicensesField] component so the same checks and changes should be applied
    on update of `invenio-rdm-records`.

Other customisations have used the [APP_RDM_DEPOSIT_FORM_DEFAULTS] setting (set in
`site/ic_data_repo/config/settings.py`). In summary:

- `resource_type` has been set to "dataset".
- `publication_data` is set to the current date.
- `rights` is set to the CC-BY-4.0 license.
- `publisher` is set to "Imperial College London".
- `creators` is set to the logged in user.

## Authentication

Authentication via Imperial SSO is handled by the `ic_data_repo.auth.oauth` module. This
implements an `info_handler` function that extracts user information the SSO response.
Relevant settings for are set in `ic_data_repo.config.settings`.

[app_rdm_deposit_form_defaults]: https://github.com/inveniosoftware/invenio-app-rdm/blob/af193c7a5fcb728343c7898ac4f52a5a5b44c95a/invenio_app_rdm/config.py#L917-L940
[creatibutorsfield]: https://github.com/inveniosoftware/invenio-rdm-records/blob/v10.9.1/invenio_rdm_records/assets/semantic-ui/js/invenio_rdm_records/src/deposit/fields/CreatibutorsField/CreatibutorsField.js
[inveniordm docs: how to override ui react components]: https://inveniordm.docs.cern.ch/develop/howtos/override_components/
[licensesfield]: https://github.com/inveniosoftware/invenio-rdm-records/blob/v10.9.1/invenio_rdm_records/assets/semantic-ui/js/invenio_rdm_records/src/deposit/fields/License/LicenseField.js
[pr #97]: https://github.com/ImperialCollegeLondon/fair-data-repository/pull/97/files
