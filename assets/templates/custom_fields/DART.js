import React, { Component } from "react";
import PropTypes from "prop-types";
import { Input } from "react-invenio-forms";
import { Form } from "semantic-ui-react";

export class DART extends Component {
  render() {
    const {
      fieldPath,
      icon,
      description,
      label,
      ID,
    } = this.props;

    return (
      <Form.Field style={{ margin: "1rem 0" }} required>
        <Input
          fieldPath={`${fieldPath}`}
          label={ID?.label || "DartId"}
          placeholder={ID?.placeholder || "Enter DartId"}
          required={ID?.required || true}
        />
        <div style={{ margin: "0.5rem 0", color: "#666" }}>
          <p>
            Please enter your DART ID. For info about DART{" "}
            <a
              href="https://www.imperial.ac.uk/admin-services/secretariat/policies-and-guidance/data-assessments/"
              target="_blank"
              rel="noopener noreferrer"
            >
              read here
            </a>
          </p>
        </div>
      </Form.Field>
    );
  }
}
