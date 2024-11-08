import React, { Component } from "react";
import {
  CreatibutorsField,
  sortOptions,
} from "@js/invenio_rdm_records";
import { CreatibutorsFieldItem } from "@js/invenio_rdm_records/src/deposit/fields/CreatibutorsField/CreatibutorsFieldItem";
import { CreatibutorsModal } from "@js/invenio_rdm_records/src/deposit/fields/CreatibutorsField/CreatibutorsModal";
import { CreatibutorsIdentifiers } from "@js/invenio_rdm_records/src/deposit/fields/CreatibutorsField/CreatibutorsIdentifiers";
import { CREATIBUTOR_TYPE } from "@js/invenio_rdm_records/src/deposit/fields/CreatibutorsField/type";
import { AffiliationsField } from "@js/invenio_rdm_records/src/deposit/fields/AffiliationsField";
import _get from "lodash/get";
import _map from "lodash/map";
import _isEmpty from "lodash/isEmpty";
import PropTypes from "prop-types";
import { Formik } from "formik";
import { getIn, FieldArray } from "formik";
import { Button, Form, Label, List, Modal, Icon } from "semantic-ui-react";
import { HTML5Backend } from "react-dnd-html5-backend";
import { DndProvider } from "react-dnd";
import {
  FieldLabel,
  SelectField,
  Image,
  RadioField,
  RemoteSelectField,
  TextField,
 } from "react-invenio-forms";
import { i18next } from "@translations/invenio_rdm_records/i18next";

const creatibutorNameDisplay = (value) => {
  const creatibutorType = _get(value, "person_or_org.type", CREATIBUTOR_TYPE.PERSON);
  const isPerson = creatibutorType === CREATIBUTOR_TYPE.PERSON;

  const familyName = _get(value, "person_or_org.family_name", "");
  const givenName = _get(value, "person_or_org.given_name", "");
  const affiliationName = _get(value, `affiliations[0].name`, "");
  const name = _get(value, `person_or_org.name`);

  const affiliation = affiliationName ? ` (${affiliationName})` : "";

  if (isPerson) {
    const givenNameSuffix = givenName ? `, ${givenName}` : "";
    return `${familyName}${givenNameSuffix}${affiliation}`;
  }

  return `${name}${affiliation}`;
};


const ModalActions = {
  ADD: "add",
  EDIT: "edit",
};

const NamesAutocompleteOptions = {
  SEARCH: "search",
  SEARCH_ONLY: "search_only",
  OFF: "off",
};

class OptionalRoleCreatibutorsModal extends CreatibutorsModal {
  render() {
    const { initialCreatibutor, autocompleteNames, roleOptions, trigger, action, includeRole} =
      this.props;
    const {
      open,
      showPersonForm,
      personIdentifiers,
      personAffiliations,
      organizationIdentifiers,
      organizationAffiliations,
      saveAndContinueLabel,
    } = this.state;

    const ActionLabel = this.displayActionLabel();
    return (
      <Formik
        initialValues={this.deserializeCreatibutor(initialCreatibutor)}
        onSubmit={this.onSubmit}
        enableReinitialize
        validationSchema={this.CreatorSchema}
        validateOnChange={false}
        validateOnBlur={false}
      >
        {({ values, resetForm, handleSubmit }) => {
          const personOrOrgPath = `person_or_org`;
          const typeFieldPath = `${personOrOrgPath}.type`;
          const familyNameFieldPath = `${personOrOrgPath}.family_name`;
          const givenNameFieldPath = `${personOrOrgPath}.given_name`;
          const organizationNameFieldPath = `${personOrOrgPath}.name`;
          const identifiersFieldPath = `${personOrOrgPath}.identifiers`;
          const affiliationsFieldPath = "affiliations";
          const roleFieldPath = "role";
          return (
            <Modal
              centered={false}
              onOpen={() => this.openModal()}
              open={open}
              trigger={trigger}
              onClose={() => {
                this.closeModal();
                resetForm();
              }}
              closeIcon
              closeOnDimmerClick={false}
            >
              <Modal.Header as="h2" className="pt-10 pb-10">
                {ActionLabel}
              </Modal.Header>
              <Modal.Content>
                <Form>
                  <Form.Group>
                    <RadioField
                      fieldPath={typeFieldPath}
                      label={i18next.t("Person")}
                      checked={_get(values, typeFieldPath) === CREATIBUTOR_TYPE.PERSON}
                      value={CREATIBUTOR_TYPE.PERSON}
                      onChange={({ formikProps }) => {
                        this.setState({
                          isOrganization: false,
                        });
                        formikProps.form.setFieldValue(
                          typeFieldPath,
                          CREATIBUTOR_TYPE.PERSON
                        );
                        formikProps.form.setFieldValue(
                          identifiersFieldPath,
                          personIdentifiers
                        );
                        formikProps.form.setFieldValue(
                          affiliationsFieldPath,
                          personAffiliations
                        );
                      }}
                      // eslint-disable-next-line
                      autoFocus
                      optimized
                    />
                    <RadioField
                      fieldPath={typeFieldPath}
                      label={i18next.t("Organization")}
                      checked={
                        _get(values, typeFieldPath) === CREATIBUTOR_TYPE.ORGANIZATION
                      }
                      value={CREATIBUTOR_TYPE.ORGANIZATION}
                      onChange={({ formikProps }) => {
                        this.setState({
                          isOrganization: true,
                        });
                        formikProps.form.setFieldValue(
                          typeFieldPath,
                          CREATIBUTOR_TYPE.ORGANIZATION
                        );
                        formikProps.form.setFieldValue(
                          affiliationsFieldPath,
                          organizationAffiliations
                        );
                        formikProps.form.setFieldValue(
                          identifiersFieldPath,
                          organizationIdentifiers
                        );
                      }}
                      optimized
                    />
                  </Form.Group>
                  {_get(values, typeFieldPath, "") === CREATIBUTOR_TYPE.PERSON ? (
                    <div>
                      {autocompleteNames !== NamesAutocompleteOptions.OFF && (
                        <RemoteSelectField
                          selectOnBlur={false}
                          selectOnNavigation={false}
                          searchInput={{
                            autoFocus: _isEmpty(initialCreatibutor),
                          }}
                          fieldPath="creators"
                          clearable
                          multiple={false}
                          allowAdditions={false}
                          placeholder={i18next.t(
                            "Search for persons by name, identifier, or affiliation..."
                          )}
                          noQueryMessage={i18next.t(
                            "Search for persons by name, identifier, or affiliation..."
                          )}
                          required={false}
                          // Disable UI-side filtering of search results
                          search={(options) => options}
                          suggestionAPIUrl="/api/names"
                          serializeSuggestions={this.serializeSuggestions}
                          onValueChange={this.onPersonSearchChange}
                          ref={this.namesAutocompleteRef}
                        />
                      )}
                      {showPersonForm && (
                        <div>
                          <Form.Group widths="equal">
                            <TextField
                              label={i18next.t("Family name")}
                              placeholder={i18next.t("Family name")}
                              fieldPath={familyNameFieldPath}
                              required={this.isCreator()}
                            />
                            <TextField
                              label={i18next.t("Given names")}
                              placeholder={i18next.t("Given names")}
                              fieldPath={givenNameFieldPath}
                            />
                          </Form.Group>
                          <CreatibutorsIdentifiers
                            initialOptions={_map(
                              _get(values, identifiersFieldPath, []),
                              (identifier) => ({
                                text: identifier,
                                value: identifier,
                                key: identifier,
                              })
                            )}
                            fieldPath={identifiersFieldPath}
                            ref={this.identifiersRef}
                          />
                          <AffiliationsField
                            fieldPath={affiliationsFieldPath}
                            selectRef={this.affiliationsRef}
                          />
                        </div>
                      )}
                    </div>
                  ) : (
                    <>
                      {autocompleteNames !== NamesAutocompleteOptions.OFF && (
                        <RemoteSelectField
                          selectOnBlur={false}
                          selectOnNavigation={false}
                          searchInput={{
                            autoFocus: _isEmpty(initialCreatibutor),
                          }}
                          fieldPath="creators"
                          clearable
                          multiple={false}
                          allowAdditions={false}
                          placeholder={i18next.t(
                            "Search for an organization by name, identifier, or affiliation..."
                          )}
                          noQueryMessage={i18next.t(
                            "Search for organization by name, identifier, or affiliation..."
                          )}
                          required={false}
                          // Disable UI-side filtering of search results
                          search={(options) => options}
                          suggestionAPIUrl="/api/affiliations"
                          serializeSuggestions={this.serializeSuggestions}
                          onValueChange={this.onOrganizationSearchChange}
                        />
                      )}
                      <TextField
                        label={i18next.t("Name")}
                        placeholder={i18next.t("Organization name")}
                        fieldPath={organizationNameFieldPath}
                        required={this.isCreator()}
                        // forward ref to Input component because Form.Input
                        // doesn't handle it
                        input={{ ref: this.inputRef }}
                      />
                      <CreatibutorsIdentifiers
                        initialOptions={_map(
                          _get(values, identifiersFieldPath, []),
                          (identifier) => ({
                            text: identifier,
                            value: identifier,
                            key: identifier,
                          })
                        )}
                        fieldPath={identifiersFieldPath}
                        ref={this.identifiersRef}
                        placeholder={i18next.t("e.g. ROR, ISNI or GND.")}
                      />
                      <AffiliationsField
                        fieldPath={affiliationsFieldPath}
                        selectRef={this.affiliationsRef}
                      />
                    </>
                  )}
                  {(_get(values, typeFieldPath) === CREATIBUTOR_TYPE.ORGANIZATION ||
                    (showPersonForm &&
                      _get(values, typeFieldPath) === CREATIBUTOR_TYPE.PERSON)) && includeRole && (
                    <div>
                      <SelectField
                        fieldPath={roleFieldPath}
                        label={i18next.t("Role")}
                        options={roleOptions}
                        placeholder={i18next.t("Select role")}
                        {...(this.isCreator() && { clearable: true })}
                        required={!this.isCreator()}
                        optimized
                        scrolling
                      />
                    </div>
                  )}
                </Form>
              </Modal.Content>
              <Modal.Actions>
                <Button
                  name="cancel"
                  onClick={() => {
                    resetForm();
                    this.closeModal();
                  }}
                  icon="remove"
                  content={i18next.t("Cancel")}
                  floated="left"
                />
                {action === ModalActions.ADD && (
                  <Button
                    name="submit"
                    onClick={() => {
                      this.setState(
                        {
                          action: "saveAndContinue",
                          showPersonForm:
                            autocompleteNames !== NamesAutocompleteOptions.SEARCH_ONLY,
                        },
                        () => {
                          handleSubmit();
                        }
                      );
                    }}
                    primary
                    icon="checkmark"
                    content={saveAndContinueLabel}
                  />
                )}
                <Button
                  name="submit"
                  onClick={() => {
                    this.setState(
                      {
                        action: "saveAndClose",
                        showPersonForm:
                          autocompleteNames !== NamesAutocompleteOptions.SEARCH_ONLY,
                      },
                      () => handleSubmit()
                    );
                  }}
                  primary
                  icon="checkmark"
                  content={i18next.t("Save")}
                />
              </Modal.Actions>
            </Modal>
          );
        }}
      </Formik>
    );
  }
}




class OptionalRoleCreatibutorsFieldForm extends Component {
  handleOnContributorChange = (selectedCreatibutor) => {
    const { push: formikArrayPush } = this.props;
    formikArrayPush(selectedCreatibutor);
  };

  render() {
    const {
      form: { values, errors, initialErrors, initialValues },
      remove: formikArrayRemove,
      replace: formikArrayReplace,
      move: formikArrayMove,
      name: fieldPath,
      label,
      labelIcon,
      roleOptions,
      schema,
      modal,
      autocompleteNames,
      addButtonLabel,
      includeRole,
      helpText,
    } = this.props;

    const creatibutorsList = getIn(values, fieldPath, []);
    const formikInitialValues = getIn(initialValues, fieldPath, []);

    const error = getIn(errors, fieldPath, null);
    const initialError = getIn(initialErrors, fieldPath, null);
    const creatibutorsError =
      error || (creatibutorsList === formikInitialValues && initialError);

    return (
      <DndProvider backend={HTML5Backend}>
        <Form.Field
          required={schema === "creators"}
          className={creatibutorsError ? "error" : ""}
        >
          <FieldLabel htmlFor={fieldPath} icon={labelIcon} label={label} />
          <List>
            {creatibutorsList.map((value, index) => {
              const key = `${fieldPath}.${index}`;
              const identifiersError =
                creatibutorsError &&
                creatibutorsError[index]?.person_or_org?.identifiers;
              const displayName = creatibutorNameDisplay(value);

              return (
                <CreatibutorsFieldItem
                  key={key}
                  identifiersError={identifiersError}
                  {...{
                    displayName,
                    index,
                    roleOptions,
                    schema,
                    compKey: key,
                    initialCreatibutor: value,
                    removeCreatibutor: formikArrayRemove,
                    replaceCreatibutor: formikArrayReplace,
                    moveCreatibutor: formikArrayMove,
                    addLabel: modal.addLabel,
                    editLabel: modal.editLabel,
                    autocompleteNames: autocompleteNames,
                  }}
                />
              );
            })}
          </List>
          <OptionalRoleCreatibutorsModal
            onCreatibutorChange={this.handleOnContributorChange}
            action="add"
            addLabel={modal.addLabel}
            editLabel={modal.editLabel}
            roleOptions={sortOptions(roleOptions)}
            schema={schema}
            autocompleteNames={autocompleteNames}
            trigger={
              <Button type="button" icon labelPosition="left">
                <Icon name="add" />
                {addButtonLabel}
              </Button>
            }
            includeRole={includeRole}
          />
          {creatibutorsError && typeof creatibutorsError == "string" && (
            <Label pointing="left" prompt>
              {creatibutorsError}
            </Label>
          )}
        </Form.Field>
        {
          // eslint-disable-next-line jsx-a11y/label-has-associated-control
          helpText && <label className="helptext">{helpText}</label>
        }
      </DndProvider>
    );
  }
}



export class OptionalRoleCreatibutorsField extends CreatibutorsField {
  render() {
    const { fieldPath } = this.props;
    return (
      <FieldArray
        name={fieldPath}
        component={(formikProps) => (
          <OptionalRoleCreatibutorsFieldForm {...formikProps} {...this.props} />
        )}
      />
    );
  }
}

OptionalRoleCreatibutorsField.propTypes = {
  includeRole: PropTypes.bool,
  helpText: PropTypes.sting,
  ...CreatibutorsField.propTypes,
}

OptionalRoleCreatibutorsField.defaultProps = {
  includeRole: true,
  helpText: "",
  ...CreatibutorsField.defaultProps,
}
