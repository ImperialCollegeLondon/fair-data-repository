
// This file is part of Invenio-RDM-Records
// Copyright (C) 2020-2023 CERN.
// Copyright (C) 2020-2022 Northwestern University.
// Copyright (C) 2021 Graz University of Technology.
//
// Invenio-RDM-Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import { Button, List } from "semantic-ui-react";
import _truncate from "lodash/truncate";
import { i18next } from "@translations/invenio_rdm_records/i18next";
import PropTypes from "prop-types";

export const LimitedLicenseFieldItem = ({
  license,
  removeLicense,
}) => {
  return (
    <List.Item key={license.key} className="deposit-listitem">
      <List.Content floated="right">
        <Button
          size="mini"
          type="button"
          onClick={() => {
            removeLicense(license.index);
          }}
        >
          {i18next.t("Remove")}
        </Button>
      </List.Content>
      <List.Content>
        <List.Header>{license.title}</List.Header>
        {license.description && (
          <List.Description>
            {_truncate(license.description, { length: 300 })}
          </List.Description>
        )}
        {license.link && (
          <span>
            <a href={license.link} target="_blank" rel="noopener noreferrer">
              {license.description && <span>&nbsp;</span>}
              {i18next.t("Read more")}
            </a>
          </span>
        )}
      </List.Content>
    </List.Item>
  );
};

LimitedLicenseFieldItem.propTypes = {
  license: PropTypes.object.isRequired,
  removeLicense: PropTypes.func.isRequired,
};
