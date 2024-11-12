import React, { Component } from "react";
import { Field, FastField } from "formik";
import { Input, Form } from "semantic-ui-react";
import PropTypes from "prop-types";


export class HiddenField extends Component {
  render() {
    const {
      fieldPath,
      error,
      helpText,
      disabled,
      label,
      optimized,
      required,
      ...uiProps
    } = this.props;
    const FormikField = optimized ? FastField : Field;

    return (
      <>
        <FormikField
          id={fieldPath}
          name={fieldPath}
        >
          {({ field, meta }) => {
            return (
              <Form.Input
                type="hidden"
                {...field}
                error={
                  error ||
                  meta.error ||
                  // We check if initialValue changed to display the initialError,
                  // otherwise it would be displayed despite updating the field
                  (!meta.touched && meta.initialError)
                }
                fluid
                id={fieldPath}
                required={required}
              />
            );
          }}
        </FormikField>
      </>
    );
  }
}

HiddenField.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  error: PropTypes.any,
  optimized: PropTypes.bool,
  required: PropTypes.bool,
};

HiddenField.defaultProps = {
  error: undefined,
  optimized: false,
  required: false,
};
