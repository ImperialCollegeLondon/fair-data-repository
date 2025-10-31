import React from "react";
import { Card, Grid } from "semantic-ui-react";
import {
  DepositStatusBox,
  PreviewButton,
  SaveButton,
  PublishButton,
} from "@js/invenio_rdm_records";
import { ShareDraftButton } from "@js/invenio_app_rdm/deposit/ShareDraftButton";
import { DepositStatus } from "@js/invenio_rdm_records/src/deposit/state/reducers/deposit";

/*
  Controls display of the form controls based on a deposit's status

  In this case there is no single Component that is being overridden so the
  return content function is copied from the
  InvenioAppRdm.Deposit.CardDepositStatusBox.container section of the RDMDepositForm
  class. We simply return null if the deposit is declined.
*/

export function ConditionalCardDepositStatusBox({
  record,
  permissions,
  groupsEnabled,
}) {
  if (record.status === DepositStatus.DECLINED) {
    return null;
  }
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
