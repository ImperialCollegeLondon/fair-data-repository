// This file is part of InvenioRDM
// Copyright (C) 2023 CERN.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { Component } from "react";
import { HiddenField } from "../../ic_data_repo/HiddenField";
import { OptionalRoleCreatibutorsField } from "../../ic_data_repo/OptionalRoleCreatibutors";
import { LimitedLicenseField } from "../../ic_data_repo/LimitedLicenseField";
import { MandatoryPIDField } from "../../ic_data_repo/MandatoryPIDField";
import { parametrize } from "react-overridable";
import { TextAreaField } from "react-invenio-forms";
import { CardDepositStatusBox } from "../../ic_data_repo/CardDepositStatusBox";
import { FundingField } from "../../ic_data_repo/Funding/FundingField";

const CreatorsField = parametrize(OptionalRoleCreatibutorsField, {
  helpText: "The main individuals or institutions involved in creating the data set.",
  includeRole: false,
});

const ContributorsField = parametrize(OptionalRoleCreatibutorsField, {
  helpText:
    "Individuals or institutions, in addition to the creators, responsible for collecting, managing, distributing or other-wise contributing to the development of the resource.",
  includeRole: true,
});

/* A simple empty element to remove non-field components via override */
class NullElement extends Component {
  render() {
    return null;
  }
}

export const overriddenComponents = {
  "InvenioAppRdm.Deposit.ContributorsField.container": ContributorsField,
  "InvenioAppRdm.Deposit.CreatorsField.container": CreatorsField,
  "InvenioAppRdm.Deposit.PIDField.container": MandatoryPIDField,
  "InvenioAppRdm.Deposit.ResourceTypeField.container": HiddenField,
  "InvenioAppRdm.Deposit.PublisherField.container": HiddenField,
  "InvenioAppRdm.Deposit.PublicationDateField.container": HiddenField,
  "InvenioAppRdm.Deposit.DescriptionsField.container": TextAreaField,
  "InvenioAppRdm.Deposit.LicenseField.container": LimitedLicenseField,
  "InvenioAppRdm.Deposit.AccordionFieldReferences.container": HiddenField,
  "InvenioAppRdm.Deposit.CommunityHeader.container": NullElement,
  "InvenioAppRdm.DashboardUploads.EmptyResults.element": NullElement,
  "InvenioAppRdm.Deposit.CardDepositStatusBox.container": CardDepositStatusBox,
  "InvenioAppRdm.Deposit.FundingField.container": FundingField,
};
