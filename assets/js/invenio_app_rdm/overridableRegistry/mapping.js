// This file is part of InvenioRDM
// Copyright (C) 2023 CERN.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { OptionalRoleCreatibutorsField } from "../../ic_data_repo/OptionalRoleCreatibutors";
import { parametrize } from "react-overridable";

const CreatorsField = parametrize(OptionalRoleCreatibutorsField, {
    helpText: "The main individuals or institutions involved in creating the data set.",
    includeRole: false,
});

export const overriddenComponents = {
    "InvenioAppRdm.Deposit.ContributorsField.container": OptionalRoleCreatibutorsField,
    "InvenioAppRdm.Deposit.CreatorsField.container": CreatorsField,
};
