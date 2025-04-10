import React, { Component } from "react";

import { Input, Array } from "react-invenio-forms";
import { Grid, Form, Button, Icon } from "semantic-ui-react";

const newDataset = {
  DartId: "",
};

export class Datasets extends Component {
  render() {
    const {
      fieldPath, // injected by the custom field loader via the field config property
      DartId,
      icon,
      addButtonLabel,
      description,
      label,
    } = this.props;

return (
  <Array
  fieldPath={fieldPath}
  DartId={DartId}
  label={label}
  icon={icon}
  addButtonLabel={addButtonLabel}
  defaultNewValue={{ DartId: "", description: "" }} // include description here if desired
  description={description}
>
  {({ arrayHelpers, indexPath }) => {
    const fieldPathPrefix = `${fieldPath}.${indexPath}`;
    return (
      <Grid style={{ border: "white 3px solid", padding: "1.5rem", backgroundColor: "#eee", margin: "1rem" }}>
        <Grid.Row>
          <Grid.Column width="15">
            <Input
              fieldPath={`${fieldPathPrefix}.DartId`}
              label="DartId"
              placeholder="Enter DartId"
            />
          </Grid.Column>
          <Grid.Column width="1">
            <Form.Field style={{ marginTop: "1.75rem", float: "right" }}>
              <Button
                aria-label="Remove field"
                className="close-btn"
                icon
                onClick={() => arrayHelpers.remove(indexPath)}
                type="button"
              >
                <Icon name="close" />
              </Button>
            </Form.Field>
          </Grid.Column>
        </Grid.Row>
        <Grid.Row>
          <Grid.Column width="16">
            <p>Please enter your DART id. For info about DART
              <a href="https://www.imperial.ac.uk/admin-services/secretariat/policies-and-guidance/data-assessments/" target="_blank" rel="noopener noreferrer">
                read more
              </a>
            </p>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    );
  }}
</Array>
);
  }
}
