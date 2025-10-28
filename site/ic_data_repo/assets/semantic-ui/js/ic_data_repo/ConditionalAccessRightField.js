import React, { Component } from "react";
import { connect } from "react-redux";
import { AccessRightField } from "@js/invenio_rdm_records";
import PropTypes from "prop-types";
import { DepositStatus } from "@js/invenio_rdm_records/src/deposit/state/reducers/deposit";

/*
Controls display of the Invenio AccessRightField component based on the deposit's status
*/
class ConditionalAccessRightFieldComponent extends Component {
  render() {
    {
      /*
      When used in the form override the props for AccessRightField component are passed
      to this one. We pull out the additional `declined` prop that has been added for
      this component and pass through the rest to AccessRightField.
      */
    }
    const { declined, ...pass_through_props } = this.props;
    if (declined) {
      return null;
    }
    return <AccessRightField {...pass_through_props} />;
  }
}

ConditionalAccessRightFieldComponent.propTypes = {
  declined: PropTypes.bool.isRequired,
  ...AccessRightField.propTypes,
};

const mapStateToProps = (state) => ({
  declined: state.deposit.record.status == DepositStatus.DECLINED,
});

export const ConditionalAccessRightField = connect(mapStateToProps)(
  ConditionalAccessRightFieldComponent,
);
