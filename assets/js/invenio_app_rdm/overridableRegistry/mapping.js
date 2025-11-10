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
import { ConditionalCardDepositStatusBox } from "../../ic_data_repo/ConditionalCardDepositStatusBox";
import { ConditionalDeleteButton } from "../../ic_data_repo/ConditionalDeleteButton";
import { ConditionalAccessRightField } from "../../ic_data_repo/ConditionalAccessRightField";

const CreatorsField = parametrize(OptionalRoleCreatibutorsField, {
  helpText:
    "The main individuals or institutions involved in creating the data set.",
  includeRole: false,
});
const DataDepositAgreement = ({ url }) => {
  const safeUrl = validateHttpUrl(url);
  return (
    <>
      <p>
        By publishing, you agree to our{" "}
        {safeUrl ? (
          <a href={safeUrl} target="_blank" rel="noopener noreferrer nofollow">
            data deposit agreement
          </a>
        ) : (
          "data deposit agreement"
        )}
        .
      </p>
    </>
  );
};

// Strict allowlist validator for http/https URLs
const validateHttpUrl = (value) => {
  if (typeof value !== "string") return "";
  const s = value.trim();
  if (!s) return "";
  try {
    const u = new URL(s, window.location.origin);
    const proto = (u.protocol || "").toLowerCase();
    return proto === "http:" || proto === "https:" ? u.toString() : "";
  } catch {
    return "";
  }
};

// Helper to read the URL from the hidden input (value may be JSON-encoded)
const getDepositAgreementURL = () => {
  const el = document.querySelector('input[name="data_deposit_agreement_url"]');
  if (!el) return "";
  let raw = el.value;
  try {
    const parsed = JSON.parse(el.value);
    raw = typeof parsed === "string" ? parsed : "";
  } catch {
    // non-JSON string is fine; use as-is
  }
  return validateHttpUrl(raw);
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
  "InvenioAppRdm.Deposit.CardDepositStatusBox.container":
    ConditionalCardDepositStatusBox,
  "InvenioAppRdm.Deposit.CardDeleteButton.container": ConditionalDeleteButton,
  "InvenioAppRdm.Deposit.AccessRightField.container": ConditionalAccessRightField,
};
