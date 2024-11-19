// This file is part of Invenio-RDM-Records
// Copyright (C) 2020-2023 CERN.
// Copyright (C) 2020-2022 Northwestern University.
// Copyright (C) 2021 Graz University of Technology.
//
// Invenio-RDM-Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { i18next } from "@translations/invenio_rdm_records/i18next";
import { Formik } from "formik";
import PropTypes from "prop-types";
import React, { Component } from "react";
import { TextAreaField, TextField } from "react-invenio-forms";
import { OverridableContext } from "react-overridable";
import {
  EmptyResults,
  Error,
  InvenioSearchApi,
  ReactSearchKit,
  ResultsLoader,
  Toggle,
} from "react-searchkit";
import { Button, Form, Grid, Menu, Modal } from "semantic-ui-react";
import * as Yup from "yup";
import { LicenseFilter } from "@js/invenio_rdm_records/src/deposit/fields/License/LicenseFilter";
import { LicenseResults } from "@js/invenio_rdm_records/src/deposit/fields/License/LicenseResults";
import { LicenseSearchBar } from "@js/invenio_rdm_records/src/deposit/fields/License/LicenseSearchBar";

const overriddenComponents = {
  "SearchFilters.Toggle": LicenseFilter,
};

const ModalActions = {
  ADD: "add",
  EDIT: "edit",
};

const LicenseSchema = Yup.object().shape({
  selectedLicense: Yup.object().shape({
    title: Yup.string().required(i18next.t("Title is a required field.")),
    link: Yup.string().url(i18next.t("Link must be a valid URL")),
  }),
});

export class LimitedLicenseModal extends Component {
  state = {
    open: false,
  };

  openModal = () => {
    this.setState({ open: true });
  };

  closeModal = () => {
    this.setState({ open: false });
  };

  onSubmit = (values, formikBag) => {
    // We have to close the modal first because onLicenseChange and passing
    // license as an object makes React get rid of this component. Otherwise
    // we get a memory leak warning.
    const { onLicenseChange } = this.props;
    this.closeModal();
    onLicenseChange(values.selectedLicense);
    formikBag.resetForm();
  };

  render() {
    const {
      licenses,
      trigger,
      action,
      searchConfig,
      serializeLicenses,
      initialLicense: initialLicenseProp,
    } = this.props;
    const { open } = this.state;

    const initialLicense = initialLicenseProp || {
      title: "",
      description: "",
      id: null,
      link: "",
    };

    // Do not display the add button if a license has been selected
    if(licenses)
        return null;

    const searchApi = new InvenioSearchApi(searchConfig.searchApi);
    return (
      <Formik
        initialValues={{
          selectedLicense: initialLicense,
        }}
        onSubmit={this.onSubmit}
        validationSchema={LicenseSchema}
        validateOnChange={false}
        validateOnBlur={false}
      >
        {({ handleSubmit, resetForm }) => (
          <Modal
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
              {action === ModalActions.ADD
                ? i18next.t(`Add license`)
                : i18next.t(`Change license`)}
            </Modal.Header>
            <Modal.Content scrolling>
                <OverridableContext.Provider value={overriddenComponents}>
                  <ReactSearchKit
                    searchApi={searchApi}
                    appName="licenses"
                    urlHandlerApi={{ enabled: false }}
                    initialQueryState={searchConfig.initialQueryState}
                  >
                    <Grid>
                      <Grid.Row verticalAlign="middle">
                        <Grid.Column>
                          <ResultsLoader>
                            <EmptyResults />
                            <Error />
                            <LicenseResults
                              {...(serializeLicenses && {
                                serializeLicenses,
                              })}
                            />
                          </ResultsLoader>
                        </Grid.Column>
                      </Grid.Row>
                    </Grid>
                  </ReactSearchKit>
                </OverridableContext.Provider>
            </Modal.Content>
            <Modal.Actions>
              <Button
                name="cancel"
                onClick={() => {
                  resetForm();
                  this.closeModal();
                }}
                icon="remove"
                labelPosition="left"
                content={i18next.t("Cancel")}
                floated="left"
              />
              <Button
                name="submit"
                onClick={(event) => handleSubmit(event)}
                primary
                icon="checkmark"
                labelPosition="left"
                content={
                  action === ModalActions.ADD
                    ? i18next.t("Add license")
                    : i18next.t("Change license")
                }
              />
            </Modal.Actions>
          </Modal>
        )}
      </Formik>
    );
  }
}

LimitedLicenseModal.propTypes = {
  action: PropTypes.oneOf(["add", "edit"]).isRequired,
  initialLicense: PropTypes.shape({
    id: PropTypes.string,
    title: PropTypes.string,
    description: PropTypes.string,
  }),
  trigger: PropTypes.object.isRequired,
  onLicenseChange: PropTypes.func.isRequired,
  searchConfig: PropTypes.shape({
    searchApi: PropTypes.shape({
      axios: PropTypes.shape({
        headers: PropTypes.object,
      }),
    }).isRequired,
    initialQueryState: PropTypes.shape({
      filters: PropTypes.arrayOf(PropTypes.array),
    }).isRequired,
  }).isRequired,
  serializeLicenses: PropTypes.func,
};

LimitedLicenseModal.defaultProps = {
  initialLicense: undefined,
  serializeLicenses: undefined,
};
