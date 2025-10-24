// This file is part of InvenioRDM
// Copyright (C) 2023 CERN.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import { Component } from "react";
import { HiddenField } from "../../ic_data_repo/HiddenField";
import { OptionalRoleCreatibutorsField } from "../../ic_data_repo/OptionalRoleCreatibutors";
import { LimitedLicenseField } from "../../ic_data_repo/LimitedLicenseField";
import { MandatoryPIDField } from "../../ic_data_repo/MandatoryPIDField";
import { parametrize } from "react-overridable";
import { TextAreaField } from "react-invenio-forms";
import { FundingField } from "../../ic_data_repo/Funding/FundingField";
import { RelatedWorksField } from "../../ic_data_repo/RelatedWorksField";
import { i18next } from "@translations/invenio_app_rdm/i18next";
import { SubmitReviewModal } from "@js/invenio_rdm_records";

const CreatorsField = parametrize(OptionalRoleCreatibutorsField, {
  helpText:
    "The main individuals or institutions involved in creating the data set.",
  includeRole: false,
});
const DataDepositAgreement = ({ url }) => (
  <>
    <p>
      By publishing, you agree to our{" "}
      <a href={url || "#"} target="_blank" rel="noopener noreferrer">
        data deposit agreement
      </a>
      .
    </p>
  </>
);
// Helper to read the URL from the hidden input (value is JSON-encoded)
const getDepositAgreementURL = () => {
  const el = document.querySelector('input[name="data_deposit_agreement_url"]');
  if (!el) return "";
  let value;
  try {
    value = JSON.parse(el.value) || "";
  } catch {
    value = el.value || "";
  }
  return value;
};

const ContributorsField = parametrize(OptionalRoleCreatibutorsField, {
  helpText:
    "Individuals or institutions, in addition to the creators, responsible for collecting, managing, distributing or other-wise contributing to the development of the resource.",
  includeRole: true,
});

const DescriptionField = parametrize(TextAreaField, { required: true });

/* A simple empty element to remove non-field components via override */
class NullElement extends Component {
  render() {
    return null;
  }
}

/* Add an extra checkbox to the SubmitReviewModal */
const parameters = {
  extraCheckboxes: [
    {
      fieldPath: "acceptDepositAgreement",
      text: i18next.t(
        "This deposit meets the requirements of the Data Deposit Agreement. Please see the link below for more information."
      ),
    },
  ],
  afterContent: () => <DataDepositAgreement url={getDepositAgreementURL()} />,
};
const SubmitReviewModalComponent = parametrize(SubmitReviewModal, parameters);

export const overriddenComponents = {
  "InvenioAppRdm.Deposit.ContributorsField.container": ContributorsField,
  "InvenioAppRdm.Deposit.CreatorsField.container": CreatorsField,
  "InvenioAppRdm.Deposit.PIDField.container": MandatoryPIDField,
  "InvenioAppRdm.Deposit.ResourceTypeField.container": HiddenField,
  "InvenioAppRdm.Deposit.PublisherField.container": HiddenField,
  "InvenioAppRdm.Deposit.PublicationDateField.container": HiddenField,
  "InvenioAppRdm.Deposit.DescriptionsField.container": DescriptionField,
  "InvenioAppRdm.Deposit.LicenseField.container": LimitedLicenseField,
  "InvenioAppRdm.Deposit.AccordionFieldReferences.container": HiddenField,
  "InvenioAppRdm.Deposit.CommunityHeader.container": NullElement,
  "InvenioAppRdm.DashboardUploads.EmptyResults.element": NullElement,
  "InvenioAppRdm.Deposit.FundingField.container": FundingField,
  "InvenioAppRdm.Deposit.RelatedWorksField.container": RelatedWorksField,
  "ReactInvenioDeposit.MetadataAccess.layout": NullElement,
  "InvenioRdmRecords.SubmitReviewModal.container": SubmitReviewModalComponent,
  "InvenioAppRdm.Deposit.CopyrightsField.container": HiddenField,
};
