import React, { Component } from "react";
import { Card, Container, Grid, Ref, Sticky } from "semantic-ui-react";
import { DepositStatusBox, PreviewButton, SaveButton } from "@js/invenio_rdm_records";
import PropTypes from "prop-types";
import { ShareDraftButton } from "@js/invenio_app_rdm/deposit/ShareDraftButton";
import { PublishButton } from "./PublishButton";

export class CardDepositStatusBox extends Component {
  render() {
    const { record, permissions, groupsEnabled } = this.props;
    return (
      <Card>
        <Card.Content>
          <DepositStatusBox />
        </Card.Content>
        <Card.Content>
          <Grid relaxed>
            <Grid.Column computer={8} mobile={16} className="pb-0 left-btn-col">
              <SaveButton fluid />
            </Grid.Column>

            <Grid.Column computer={8} mobile={16} className="pb-0 right-btn-col">
              <PreviewButton fluid />
            </Grid.Column>

            <Grid.Column width={16} className="pt-10">
              <PublishButton fluid record={record} />
            </Grid.Column>

            <Grid.Column width={16} className="pt-0">
              {(record.is_draft === null || permissions.can_manage) && (
                <ShareDraftButton
                  record={record}
                  permissions={permissions}
                  groupsEnabled={groupsEnabled}
                />
              )}
            </Grid.Column>
          </Grid>
        </Card.Content>
      </Card>
    );
  }
}

CardDepositStatusBox.propTypes = {
  record: PropTypes.object.isRequired,
  permissions: PropTypes.object,
  groupsEnabled: PropTypes.bool.isRequired,
};

CardDepositStatusBox.defaultProps = {
  permissions: null,
};
