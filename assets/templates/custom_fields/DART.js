import React, { Component } from "react";

import { Input } from "react-invenio-forms";
import { Grid } from "semantic-ui-react";

export class DART extends Component {
  render() {
    const {
      fieldPath, // injected by the custom field loader via the field config property
      icon,
      description,
      label,
    } = this.props;

    return (
      <Grid style={{ border: "white 3px solid", padding: "1.5rem", backgroundColor: "#eee", margin: "1rem" }}>
        <Grid.Row>
          <Grid.Column width="16">
            <Input
              fieldPath={`${fieldPath}.ID`}
              label="DartId"
              placeholder="Enter DartId"
            />
          </Grid.Column>
        </Grid.Row>
        <Grid.Row>
          <Grid.Column width="16">
            <p>
              Please enter your DART id. For info about DART{" "}
              <a
                href="https://www.imperial.ac.uk/admin-services/secretariat/policies-and-guidance/data-assessments/"
                target="_blank"
                rel="noopener noreferrer"
              >
                read more
              </a>
            </p>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    );
  }
}
