// This file is part of InvenioVocabularies
// Copyright (C) 2021-2025 CERN.
// Copyright (C) 2021 Northwestern University.
//
// Invenio is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import PropTypes from "prop-types";
import { FieldArray, getIn } from "formik";
import { HTML5Backend } from "react-dnd-html5-backend";
import { DndProvider } from "react-dnd";
import { Button, Form, Icon, List } from "semantic-ui-react";
import { FieldLabel, FeedbackLabel } from "react-invenio-forms";

import { FundingFieldItem } from "./FundingFieldItem";
import FundingModal from "./FundingModal";

import { i18next } from "@translations/invenio_rdm_records/i18next";

import Overridable from "react-overridable";

function FundingFieldForm(props) {
  const {
    label,
    labelIcon,
    fieldPath,
    form: { values, errors, initialErrors, initialValues },
    move: formikArrayMove,
    push: formikArrayPush,
    remove: formikArrayRemove,
    replace: formikArrayReplace,
    required,
    deserializeAward: deserializeAwardFunc,
    deserializeFunder: deserializeFunderFunc,
    computeFundingContents: computeFundingContentsFunc,
    searchConfig,
  } = props;

  const deserializeAward = deserializeAwardFunc
    ? deserializeAwardFunc
    : (award) => ({
        title: award?.title_l10n,
        number: award.number,
        funder: award.funder ?? "",
        id: award.id,
        ...(award.identifiers && { identifiers: award.identifiers }),
        ...(award.acronym && { acronym: award.acronym }),
      });

  const deserializeFunder = deserializeFunderFunc
    ? deserializeFunderFunc
    : (funder) => ({
        id: funder.id,
        name: funder.name,
        ...(funder.pid && { pid: funder.pid }),
        ...(funder.country && { country: funder.country }),
        ...(funder.identifiers && { identifiers: funder.identifiers }),
      });

  const computeFundingContents = computeFundingContentsFunc
    ? computeFundingContentsFunc
    : (funding) => {
        let headerContent,
          descriptionContent = "";
        let awardOrFunder = "award";
        if (funding.award) {
          headerContent = funding.award.title;
        }

        if (funding.funder) {
          const funderName =
            funding?.funder?.name ?? funding.funder?.title ?? funding?.funder?.id ?? "";
          descriptionContent = funderName;
          if (!headerContent) {
            awardOrFunder = "funder";
            headerContent = funderName;
            descriptionContent = "";
          }
        }

        return { headerContent, descriptionContent, awardOrFunder };
      };

  const fundingList = getIn(values, fieldPath, []);
  const formikInitialValues = getIn(initialValues, fieldPath, []);

  const error = getIn(errors, fieldPath, null);
  const initialError = getIn(initialErrors, fieldPath, null);
  const fundingError = error || (fundingList === formikInitialValues && initialError);

  let className = "";
  if (fundingError) {
    className = typeof fundingError !== "string" ? fundingError.severity : "error";
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <Form.Field required={required} className={className}>
        <FieldLabel htmlFor={fieldPath} icon={labelIcon} label={label} />
        <List>
          {fundingList.map((value, index) => {
            const key = `${fieldPath}.${index}`;
            // if award does not exist or has no id, it's a custom one
            const awardType = value?.award?.id ? "standard" : "custom";
            return (
              <FundingFieldItem
                key={key}
                {...{
                  index,
                  compKey: key,
                  fundingItem: value,
                  awardType,
                  moveFunding: formikArrayMove,
                  replaceFunding: formikArrayReplace,
                  removeFunding: formikArrayRemove,
                  searchConfig: searchConfig,
                  computeFundingContents: computeFundingContents,
                  deserializeAward: deserializeAward,
                  deserializeFunder: deserializeFunder,
                }}
              />
            );
          })}
        </List>

        <Overridable id="InvenioVocabularies.FundingField.AddAwardFundingModal.Container">
          <FundingModal
            searchConfig={searchConfig}
            trigger={
              <Button
                type="button"
                key="custom"
                icon
                labelPosition="left"
                className={`mb-5 ${className}`}
              >
                <Icon name="add" />
                {i18next.t("Add")}
              </Button>
            }
            onAwardChange={(selectedFunding) => {
              formikArrayPush(selectedFunding);
            }}
            mode="standard"
            action="add"
            deserializeAward={deserializeAward}
            deserializeFunder={deserializeFunder}
            computeFundingContents={computeFundingContents}
          />
        </Overridable>

        <Overridable id="InvenioVocabularies.FundingField.AddCustomFundingModal.Container">
          <FundingModal
            searchConfig={searchConfig}
            trigger={
              <Button
                type="button"
                key="custom"
                icon
                labelPosition="left"
                className={className}
              >
                <Icon name="add" />
                {i18next.t("Add custom")}
              </Button>
            }
            onAwardChange={(selectedFunding) => {
              formikArrayPush(selectedFunding);
            }}
            mode="custom"
            action="add"
            deserializeAward={deserializeAward}
            deserializeFunder={deserializeFunder}
            computeFundingContents={computeFundingContents}
          />
        </Overridable>

        {fundingError && <FeedbackLabel errorMessage={fundingError} />}
      </Form.Field>
    </DndProvider>
  );
}

FundingFieldForm.propTypes = {
  label: PropTypes.node,
  labelIcon: PropTypes.node,
  fieldPath: PropTypes.string.isRequired,
  form: PropTypes.object,
  move: PropTypes.func,
  push: PropTypes.func,
  remove: PropTypes.func,
  replace: PropTypes.func,
  required: PropTypes.bool,
  deserializeAward: PropTypes.func,
  deserializeFunder: PropTypes.func,
  computeFundingContents: PropTypes.func,
  searchConfig: PropTypes.object,
};

FundingFieldForm.defaultProps = {
  label: undefined,
  labelIcon: undefined,
  form: undefined,
  move: undefined,
  push: undefined,
  remove: undefined,
  replace: undefined,
  required: undefined,
  deserializeAward: undefined,
  deserializeFunder: undefined,
  computeFundingContents: undefined,
  searchConfig: undefined,
};

export function FundingField(props) {
  const { fieldPath } = props;
  return (
    <FieldArray
      name={fieldPath}
      component={(formikProps) => <FundingFieldForm {...formikProps} {...props} />}
    />
  );
}

FundingField.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  label: PropTypes.string,
  labelIcon: PropTypes.string,
  searchConfig: PropTypes.object.isRequired,
  required: PropTypes.bool,
  deserializeAward: PropTypes.func,
  deserializeFunder: PropTypes.func,
  computeFundingContents: PropTypes.func,
};

FundingField.defaultProps = {
  label: "Awards",
  labelIcon: "money bill alternate outline",
  required: false,
  deserializeAward: undefined,
  deserializeFunder: undefined,
  computeFundingContents: undefined,
};
