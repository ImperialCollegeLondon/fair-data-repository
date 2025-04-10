import React from "react";
import PropTypes from "prop-types";
import { Input } from "react-invenio-forms";
import { Form } from "semantic-ui-react";

export function DartIdField(props) {
  const {
    fieldPath,
    label,
    icon,
    placeholder,
    clearable,
  } = props;

  return (
    <Form.Field className="dart-id-field">
      <Input
        fieldPath={fieldPath}
        label={label}
        placeholder={placeholder}
        icon={icon}
        clearable={clearable}
      />

      <div className="help-text" style={{ marginTop: '8px', color: '#666', fontSize: '0.9em' }}>
        <p>
          The DART ID is a unique identifier assigned to datasets in the Imperial College London
          Data Assessment Repository Tool. This ID must be provided for all research data deposits.
        </p>
        <p>
          <a
            href="https://www.imperial.ac.uk/admin-services/secretariat/policies-and-guidance/data-assessments/"
            target="_blank"
            rel="noopener noreferrer"
          >
            More info
          </a>
        </p>
      </div>
    </Form.Field>
  );
}

DartIdField.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  label: PropTypes.string,
  icon: PropTypes.string,
  placeholder: PropTypes.string,
  search: PropTypes.bool,
  multiple: PropTypes.bool,
  clearable: PropTypes.bool,
};

DartIdField.defaultProps = {
  label: "DART ID",
  icon: "address card outline",
  placeholder: "DART ID",
  search: false,
  multiple: false,
  clearable: true,
};
