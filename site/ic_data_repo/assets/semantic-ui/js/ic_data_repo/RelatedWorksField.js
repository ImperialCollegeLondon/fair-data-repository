// This file is part of React-Invenio-Deposit
// Copyright (C) 2020-2021 CERN.
// Copyright (C) 2020-2022 Northwestern University.
// Copyright (C) 2021 Graz University of Technology.
//
// React-Invenio-Deposit is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { Component } from "react";
import PropTypes from "prop-types";

import {
  TextField,
  GroupField,
  ArrayField,
  FieldLabel,
  SelectField,
} from "react-invenio-forms";
import { Button, Form, Icon } from "semantic-ui-react";
import { emptyRelatedWork } from "./initialValues";
import { ResourceTypeField } from "./ResourceTypeField";
import { i18next } from "@translations/invenio_rdm_records/i18next";
import { DoiSearchModal } from "./DoiSearchModal";

export class RelatedWorksField extends Component {
  // Helper (could also be a top-level const)
  symplecticEnabled() {
    try {
      const el = document.querySelector('input[name="symplectic_search_enabled"]');
      if (!el) return false;
      return JSON.parse(el.value);
    } catch {
      return false;
    }
  }

  render() {
    const { fieldPath, label, labelIcon, required, options, showEmptyValue } =
      this.props;

    const symplecticSearchEnabled = this.symplecticEnabled();

    return (
      <>
        <label className="helptext" style={{ marginBottom: "10px" }}>
          {i18next.t(
            "Specify identifiers of related works. Supported identifiers include DOI, Handle, ARK, PURL, ISSN, ISBN, PubMed ID, PubMed Central ID, ADS Bibliographic Code, arXiv, Life Science Identifiers (LSID), EAN-13, ISTC, URNs, and URLs."
          )}
          {' '}
          <strong>
            <>
              {i18next.t("If you have a publication in")}
              {" "}
              <a
                href="https://www.imperial.ac.uk/research-and-innovation/support-for-staff/scholarly-communication/symplectic/"
                target="_blank"
                rel="noopener noreferrer"
              >
                {i18next.t("symplectic elements")}
              </a>
              {", "}
              {i18next.t(
                "you can use the Symplectic search to find the correct doi and it will make a realtionship to the related work."
              )}
            </>
          </strong>
        </label>
        <ArrayField
          addButtonLabel={i18next.t("Add related work")}
          defaultNewValue={emptyRelatedWork}
          fieldPath={fieldPath}
          label={<FieldLabel htmlFor={fieldPath} icon={labelIcon} label={label} />}
          required={required}
          showEmptyValue={showEmptyValue}
        >
          {({ arrayHelpers, indexPath, form }) => {
            const fieldPathPrefix = `${fieldPath}.${indexPath}`;

            return (
              <GroupField optimized>
                <SelectField
                  clearable
                  fieldPath={`${fieldPathPrefix}.relation_type`}
                  label={i18next.t("Relation")}
                  optimized
                  options={options.relations}
                  placeholder={i18next.t("Select relation...")}
                  required
                  width={3}
                />

                <TextField
                  fieldPath={`${fieldPathPrefix}.identifier`}
                  label={i18next.t("Identifier")}
                  required
                  width={4}
                />

                <SelectField
                  clearable
                  fieldPath={`${fieldPathPrefix}.scheme`}
                  label={i18next.t("Scheme")}
                  optimized
                  options={options.scheme}
                  required
                  width={2}
                />

                <ResourceTypeField
                  clearable
                  fieldPath={`${fieldPathPrefix}.resource_type`}
                  labelIcon="" // Otherwise breaks alignment
                  options={options.resource_type}
                  width={7}
                  labelclassname="small field-label-class"
                />

                <Form.Field>
                  <Button
                    aria-label={i18next.t("Remove field")}
                    className="close-btn"
                    icon
                    onClick={() => arrayHelpers.remove(indexPath)}
                  >
                    <Icon name="close" />
                  </Button>
                </Form.Field>

                {symplecticSearchEnabled && (
                  <DoiSearchModal
                    trigger={
                      <Button type="button" icon labelPosition="left" className="mt-10">
                        <Icon name="search" />
                        {i18next.t("Symplectic search")}
                      </Button>
                    }
                    onSelect={(selectedIdentifier) => {
                      form.setFieldValue(`${fieldPathPrefix}.identifier`, selectedIdentifier);
                      form.setFieldValue(`${fieldPathPrefix}.scheme`, "doi");
                      form.setFieldValue(`${fieldPathPrefix}.resource_type`, "publication");
                    }}
                  />
                )}
              </GroupField>
            );
          }}
        </ArrayField>
      </>
    );
  }
}

RelatedWorksField.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  label: PropTypes.string,
  labelIcon: PropTypes.string,
  required: PropTypes.bool,
  options: PropTypes.object.isRequired,
  showEmptyValue: PropTypes.bool,
};

RelatedWorksField.defaultProps = {
  label: i18next.t("Related works"),
  labelIcon: "barcode",
  required: undefined,
  showEmptyValue: false,
};
