import React, { Component } from "react";
import { connect } from "react-redux";
import { Card, Grid, Icon, Popup } from "semantic-ui-react";
import { DeleteButton } from "@js/invenio_rdm_records/src/deposit/controls/DeleteButton";
import { DepositStatus } from "@js/invenio_rdm_records/src/deposit/state/reducers/deposit";
import PropTypes from "prop-types";

/*
Controls render of the Invenio DeleteButton component based on the deposit's status

In the case of a declined deposit we display the status and suggest deletion.
*/
export class ConditionalDeleteButtonComponent extends Component {
  render() {
    const { declined } = this.props;
    return (
      <Card>
        {declined && (
          <Card.Content>
            <Grid verticalAlign="middle">
              <Grid.Row centered className="pt-5 pb-5 negative">
                <Grid.Column width={16} textAlign="center">
                  <span>Declined</span>
                  <Popup
                    trigger={<Icon className="ml-10" name="info circle" />}
                    content="This deposit has been declined for inclusion and may be deleted."
                  />
                </Grid.Column>
              </Grid.Row>
            </Grid>
          </Card.Content>
        )}
        <Card.Content>
          <DeleteButton fluid />
        </Card.Content>
      </Card>
    );
  }
}

ConditionalDeleteButtonComponent.propTypes = {
  declined: PropTypes.bool.isRequired,
};

const mapStateToProps = (state) => ({
  declined: state.deposit.record.status == DepositStatus.DECLINED,
});

export const ConditionalDeleteButton = connect(mapStateToProps)(
  ConditionalDeleteButtonComponent,
);
