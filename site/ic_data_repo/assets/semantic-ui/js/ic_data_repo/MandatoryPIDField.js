// This file is part of Invenio-RDM-Records
// Copyright (C) 2020-2023 CERN.
// Copyright (C) 2020-2022 Northwestern University.
//
// Invenio-RDM-Records is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { i18next } from "@translations/invenio_rdm_records/i18next";
import { FastField, Field, getIn } from "formik";
import PropTypes from "prop-types";
import React, { Component, Fragment } from "react";
import { FieldLabel } from "react-invenio-forms";
import { connect } from "react-redux";
import { Form, Popup } from "semantic-ui-react";
import {
  DepositFormSubmitActions,
  DepositFormSubmitContext,
} from "@js/invenio_rdm_records/src/deposit/api/DepositFormSubmitContext";
import { DISCARD_PID_STARTED, RESERVE_PID_STARTED } from "@js/invenio_rdm_records/src/deposit/state/types";

const getFieldErrors = (form, fieldPath) => {
  return (
    getIn(form.errors, fieldPath, null) || getIn(form.initialErrors, fieldPath, null)
  );
};

/**
 * Button component to reserve a PID.
 */
class ReservePIDBtn extends Component {
  render() {
    const { disabled, handleReservePID, label, loading } = this.props;
    return (
      <Field>
        {({ form: formik }) => (
          <Form.Button
            className="positive"
            size="mini"
            loading={loading}
            disabled={disabled || loading}
            onClick={(e) => handleReservePID(e, formik)}
            content={label}
          />
        )}
      </Field>
    );
  }
}

ReservePIDBtn.propTypes = {
  disabled: PropTypes.bool,
  handleReservePID: PropTypes.func.isRequired,
  label: PropTypes.string.isRequired,
  loading: PropTypes.bool,
};

ReservePIDBtn.defaultProps = {
  disabled: false,
  loading: false,
};

/**
 * Button component to unreserve a PID.
 */
class UnreservePIDBtn extends Component {
  render() {
    const { disabled, handleDiscardPID, label, loading } = this.props;
    return (
      <Popup
        content={label}
        trigger={
          <Field>
            {({ form: formik }) => (
              <Form.Button
                disabled={disabled || loading}
                loading={loading}
                icon="close"
                onClick={(e) => handleDiscardPID(e, formik)}
                size="mini"
              />
            )}
          </Field>
        }
      />
    );
  }
}

UnreservePIDBtn.propTypes = {
  disabled: PropTypes.bool,
  handleDiscardPID: PropTypes.func.isRequired,
  label: PropTypes.string.isRequired,
  loading: PropTypes.bool,
};

UnreservePIDBtn.defaultProps = {
  disabled: false,
  loading: false,
};

/**
 * Render identifier field and reserve/unreserve
 * button components for managed PID.
 */
class ManagedIdentifierComponent extends Component {
  static contextType = DepositFormSubmitContext;

  handleReservePID = (event, formik) => {
    const { pidType } = this.props;
    const { setSubmitContext } = this.context;
    setSubmitContext(DepositFormSubmitActions.RESERVE_PID, {
      pidType: pidType,
    });
    formik.handleSubmit(event);
  };

  handleDiscardPID = (event, formik) => {
    const { pidType } = this.props;
    const { setSubmitContext } = this.context;
    setSubmitContext(DepositFormSubmitActions.DISCARD_PID, {
      pidType: pidType,
    });
    formik.handleSubmit(event);
  };

  render() {
    const {
      actionState,
      actionStateExtra,
      btnLabelDiscardPID,
      btnLabelGetPID,
      disabled,
      helpText,
      identifier,
      pidType,
    } = this.props;
    const hasIdentifier = identifier !== "";

    const ReserveBtn = (
      <ReservePIDBtn
        disabled={disabled || hasIdentifier}
        label={btnLabelGetPID}
        loading={
          actionState === RESERVE_PID_STARTED && actionStateExtra.pidType === pidType
        }
        handleReservePID={this.handleReservePID}
      />
    );

    const UnreserveBtn = (
      <UnreservePIDBtn
        disabled={disabled}
        label={btnLabelDiscardPID}
        handleDiscardPID={this.handleDiscardPID}
        loading={
          actionState === DISCARD_PID_STARTED && actionStateExtra.pidType === pidType
        }
        pidType={pidType}
      />
    );

    return (
      <>
        <Form.Group inline>
          {hasIdentifier && (
            <Form.Field>
              <label>{identifier}</label>
            </Form.Field>
          )}

          <Form.Field>{identifier ? UnreserveBtn : ReserveBtn}</Form.Field>
        </Form.Group>
        {helpText && <label className="helptext">{helpText}</label>}
      </>
    );
  }
}

ManagedIdentifierComponent.propTypes = {
  btnLabelGetPID: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  helpText: PropTypes.string,
  identifier: PropTypes.string.isRequired,
  btnLabelDiscardPID: PropTypes.string.isRequired,
  pidType: PropTypes.string.isRequired,
  /* from Redux */
  actionState: PropTypes.string,
  actionStateExtra: PropTypes.object,
};

ManagedIdentifierComponent.defaultProps = {
  disabled: false,
  helpText: null,
  /* from Redux */
  actionState: "",
  actionStateExtra: {},
};

const mapStateToProps = (state) => ({
  actionState: state.deposit.actionState,
  actionStateExtra: state.deposit.actionStateExtra,
});

const ManagedIdentifierCmp = connect(mapStateToProps, null)(ManagedIdentifierComponent);

/**
 * Render managed or unmanaged PID fields and update
 * Formik form on input changed.
 * The field value has the following format:
 * { 'doi': { identifier: '<value>', provider: '<value>', client: '<value>' } }
 */
class CustomPIDField extends Component {
  constructor(props) {
    super(props);
    const { form } = props;

    // Clear the field if the DOI is external
    if ('doi' in form.values.pids && form.values.pids['doi'].provider === 'external') {
        form.setFieldValue("pids", {});
    }
  }

  render() {
    const {
      btnLabelDiscardPID,
      btnLabelGetPID,
      form,
      fieldPath,
      fieldLabel,
      isEditingPublishedRecord,
      managedHelpText,
      pidIcon,
      required,
      pidType,
      field,
      record,
    } = this.props;

    const value = field.value || {};
    // If we are editing an already published record.
    const currentIdentifier = value.identifier || "";
    const doi = record?.pids?.doi?.identifier || "";
    const hasDoi = doi !== "";
    const fieldError = getFieldErrors(form, fieldPath);

    return (
      <>
        <Form.Field required={required} error={fieldError}>
          <FieldLabel htmlFor={fieldPath} icon={pidIcon} label={fieldLabel} />
        </Form.Field>

          <ManagedIdentifierCmp
            disabled={hasDoi && isEditingPublishedRecord}
            btnLabelDiscardPID={btnLabelDiscardPID}
            btnLabelGetPID={btnLabelGetPID}
            form={form}
            identifier={currentIdentifier}
            helpText={managedHelpText}
            pidType={pidType}
          />

      </>
    );
  }
}

CustomPIDField.propTypes = {
  field: PropTypes.object,
  form: PropTypes.object.isRequired,
  btnLabelDiscardPID: PropTypes.string.isRequired,
  btnLabelGetPID: PropTypes.string.isRequired,
  fieldPath: PropTypes.string.isRequired,
  fieldLabel: PropTypes.string.isRequired,
  isEditingPublishedRecord: PropTypes.bool.isRequired,
  managedHelpText: PropTypes.string,
  pidIcon: PropTypes.string.isRequired,
  pidType: PropTypes.string.isRequired,
  required: PropTypes.bool.isRequired,
  record: PropTypes.object.isRequired,
};

CustomPIDField.defaultProps = {
  managedHelpText: null,
  field: undefined,
};


/**
 * Render the PIDField using a custom Formik component
 */
export class PIDField extends Component {
  render() {
    const { fieldPath } = this.props;
    return <FastField name={fieldPath} component={CustomPIDField} {...this.props} />;
  }
}

PIDField.propTypes = {
  btnLabelDiscardPID: PropTypes.string,
  btnLabelGetPID: PropTypes.string,
  fieldPath: PropTypes.string.isRequired,
  fieldLabel: PropTypes.string.isRequired,
  isEditingPublishedRecord: PropTypes.bool.isRequired,
  managedHelpText: PropTypes.string,
  pidIcon: PropTypes.string,
  pidType: PropTypes.string.isRequired,
  required: PropTypes.bool,
  record: PropTypes.object.isRequired,
};

PIDField.defaultProps = {
  btnLabelDiscardPID: "Discard",
  btnLabelGetPID: "Reserve",
  managedHelpText: null,
  pidIcon: "barcode",
  required: false,
};


/**
 * Render the PIDField using a custom Formik component
 */
export class MandatoryPIDField extends Component {
  render() {
    let { config, record } = this.props;

    const pids = config.pids.map((pid) => (
        <Fragment key={pid.scheme}>
          <PIDField
            btnLabelDiscardPID={pid.btn_label_discard_pid}
            btnLabelGetPID={pid.btn_label_get_pid}
            fieldPath={`pids.${pid.scheme}`}
            fieldLabel={pid.field_label}
            isEditingPublishedRecord={
              record.is_published === true // is_published is `null` at first upload
            }
            managedHelpText={pid.managed_help_text}
            pidType={pid.scheme}
            required
            record={record}
          />
        </Fragment>
      ));

    return (
        <Fragment>
            {pids}
        </Fragment>
        );
  }
}
