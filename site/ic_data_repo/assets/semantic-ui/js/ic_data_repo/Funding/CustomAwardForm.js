// This file is part of InvenioVocabularies
// Copyright (C) 2021-2024 CERN.
// Copyright (C) 2021 Northwestern University.
//
// Invenio is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import PropTypes from "prop-types";
import React from "react";
import { Form, Header } from "semantic-ui-react";
import { TextField, RemoteSelectField } from "react-invenio-forms";
import { i18next } from "@translations/invenio_rdm_records/i18next";
import _isEmpty from "lodash/isEmpty";

import Overridable from "react-overridable";

function CustomAwardForm({ deserializeFunder, selectedFunding }) {
  function deserializeFunderToDropdown(funderItem) {
    const funderName = funderItem?.name;
    const funderPID = funderItem?.id;
    const funderCountry = funderItem?.country_name ?? funderItem?.country;

    if (!funderName && !funderPID) {
      return {};
    }

    return {
      text: [funderName, funderCountry, funderPID].filter((val) => val).join(", "),
      value: funderItem.id,
      key: funderItem.id,
      ...(funderName && { name: funderName }),
      ...(funderPID && { pid: funderPID }),
    };
  }

  function serializeFunderFromDropdown(funderDropObject) {
    return {
      id: funderDropObject.key,
      ...(funderDropObject.name && { name: funderDropObject.name }),
      ...(funderDropObject.pid && { pid: funderDropObject.pid }),
    };
  }

  return (
    <Form>
      <Overridable
        id="InvenioVocabularies.CustomAwardForm.RemoteSelectField.Container"
        fieldPath="selectedFunding.funder.id"
      >
        <RemoteSelectField
          fieldPath="selectedFunding.funder.id"
          suggestionAPIUrl="/api/funders"
          suggestionAPIHeaders={{
            Accept: "application/vnd.inveniordm.v1+json",
          }}
          placeholder={i18next.t("Search for a funder by name")}
          serializeSuggestions={(funders) => {
            return funders.map((funder) =>
              deserializeFunderToDropdown(deserializeFunder(funder))
            );
          }}
          searchInput={{
            autoFocus: _isEmpty(selectedFunding),
          }}
          label={i18next.t("Funder")}
          noQueryMessage={i18next.t("Search for funder...")}
          clearable
          allowAdditions={false}
          multiple={false}
          selectOnBlur={false}
          selectOnNavigation={false}
          required
          search={(options) => options}
          isFocused
          onValueChange={({ formikProps }, selectedFundersArray) => {
            if (selectedFundersArray.length === 1) {
              const selectedFunder = selectedFundersArray[0];
              if (selectedFunder) {
                const deserializedFunder = serializeFunderFromDropdown(selectedFunder);
                formikProps.form.setFieldValue(
                  "selectedFunding.funder",
                  deserializedFunder
                );
              }
            }
          }}
        />
      </Overridable>
      <Overridable id="InvenioVocabularies.CustomAwardForm.AwardInformationHeader.Container">
        <Header as="h3" size="small">
          {i18next.t("Additional information")} ({i18next.t("optional")})
        </Header>
      </Overridable>
      <Form.Group widths="equal">
        <Overridable
          id="InvenioVocabularies.CustomAwardForm.AwardNumberTextField.Container"
          fieldPath="selectedFunding.award.number"
        >
          <TextField
            label={i18next.t("Number")}
            placeholder={i18next.t("Award/Grant number")}
            fieldPath="selectedFunding.award.number"
          />
        </Overridable>
        <Overridable
          id="InvenioVocabularies.CustomAwardForm.AwardTitleTextField.Container"
          fieldPath="selectedFunding.award.title"
        >
          <TextField
            label={i18next.t("Title")}
            placeholder={i18next.t("Award/Grant Title")}
            fieldPath="selectedFunding.award.title"
          />
        </Overridable>
        <Overridable
          id="InvenioVocabularies.CustomAwardForm.AwardUrlTextField.Container"
          fieldPath="selectedFunding.award.url"
        >
          <TextField
            label={i18next.t("URL")}
            placeholder={i18next.t("Award/Grant URL")}
            fieldPath="selectedFunding.award.url"
          />
        </Overridable>
      </Form.Group>
    </Form>
  );
}

CustomAwardForm.propTypes = {
  deserializeFunder: PropTypes.func.isRequired,
  selectedFunding: PropTypes.object,
};

CustomAwardForm.defaultProps = {
  selectedFunding: undefined,
};

export default CustomAwardForm;
