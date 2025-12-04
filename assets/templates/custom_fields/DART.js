import React, { Component } from "react";
import PropTypes from "prop-types";
import { Input } from "react-invenio-forms";
import { Form } from "semantic-ui-react";

export class DART extends Component {
  render() {
    const { fieldPath, icon, description, label, ID } = this.props;

    return (
      <Form.Field style={{ margin: "1rem 0" }}>
        <Input
          fieldPath={`${fieldPath}`}
          label={ID?.label || "DART ID"}
          placeholder={ID?.placeholder || "Enter DART ID"}
          required={false}
        />
        <div style={{ margin: "0.5rem 0", color: "#666" }}>
          <label class="helptext">
            Please enter your DART ID. For information about DART{" "}
            <a
              href="https://www.imperial.ac.uk/admin-services/secretariat/policies-and-guidance/data-assessments/"
              target="_blank"
              rel="noopener noreferrer"
            >
              read here.
            </a>
          </label>
        </div>
      </Form.Field>
    );
  }
}
