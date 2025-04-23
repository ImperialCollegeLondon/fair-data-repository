// This file is part of InvenioVocabularies
// Copyright (C) 2021-2024 CERN.
// Copyright (C) 2021 Northwestern University.
//
// Invenio is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import PropTypes from "prop-types";
import React from "react";
import { Segment } from "semantic-ui-react";
import { i18next } from "@translations/invenio_rdm_records/i18next";

export function NoAwardResults({ switchToCustom }) {
  return (
    <Segment
      basic
      content={
        <p>
          {i18next.t("Did not find your award/grant? ")}
          <a
            href="/"
            onClick={(e) => {
              e.preventDefault();
              switchToCustom();
            }}
          >
            {i18next.t("Add a custom award/grant.")}
          </a>
        </p>
      }
    />
  );
}

NoAwardResults.propTypes = {
  switchToCustom: PropTypes.func.isRequired,
};
