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
import { OverridableContext } from "react-overridable";
import {
  EmptyResults,
  Error,
  InvenioSearchApi,
  ReactSearchKit,
  ResultsLoader,
} from "react-searchkit";
import { Button, Grid, Modal } from "semantic-ui-react";
import { LicenseModal } from "@js/invenio_rdm_records/src/deposit/fields/License/LicenseModal";
import { LicenseFilter } from "@js/invenio_rdm_records/src/deposit/fields/License/LicenseFilter";
import { LicenseResults } from "@js/invenio_rdm_records/src/deposit/fields/License/LicenseResults";

const overriddenComponents = {
  "SearchFilters.Toggle": LicenseFilter,
};

const ModalActions = {
  ADD: "add",
};

export class LimitedLicenseModal extends LicenseModal {
  render() {
    const {
      trigger,
      searchConfig,
      serializeLicenses,
    } = this.props;
    const { open } = this.state;

    const searchApi = new InvenioSearchApi(searchConfig.searchApi);
    return (
      <Formik
        initialValues={{
          selectedLicense: {
            title: "",
            description: "",
            id: null,
            link: "",
          },
        }}
        onSubmit={this.onSubmit}
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
              {i18next.t(`Add license`)}
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
                content={i18next.t("Add license")}
              />
            </Modal.Actions>
          </Modal>
        )}
      </Formik>
    );
  }
}

LimitedLicenseModal.propTypes = {
  action: PropTypes.oneOf(["add"]).isRequired,
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
  serializeLicenses: undefined,
};
