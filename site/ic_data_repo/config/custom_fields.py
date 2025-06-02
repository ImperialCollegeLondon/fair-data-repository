"""Custom fields configuration, part of the settings."""

from invenio_records_resources.services.custom_fields import TextCF
from marshmallow import validate
from marshmallow.exceptions import ValidationError
from marshmallow_utils.fields import ISOLangString

RDM_NAMESPACES = {
    "imperial": "https://www.imperial.ac.uk",
}


def dart_id_validate_numeric(val: str):
    """Check that the provided value looks like a number."""
    if not val.isnumeric():
        raise ValidationError("DART ID must be a numeric value.")


RDM_CUSTOM_FIELDS = [
    TextCF(
        name="imperial:contact_information",
        field_cls=ISOLangString,
        field_args={
            # must be an implementation of Marshmallow.validate.Validator
            "validate": validate.Email(),
        },
        multiple=False,
    ),
    TextCF(
        name="imperial:dart_id",
        field_args={
            "validate": [validate.Length(min=1, max=100), dart_id_validate_numeric],
            "required": True,
            "error_messages": {
                "required": "DART ID is required.",
                "invalid": "Invalid DART ID.",
            },
        },
        multiple=False,
    ),
]

RDM_CUSTOM_FIELDS_UI = [
    {
        "section": "Contact information",
        "fields": [
            dict(
                field="imperial:contact_information",
                ui_widget="Input",
                template="contact_information.html",
                props=dict(
                    label="Contact information",
                    placeholder="name@imperial.ic.uk",
                    icon="address card outline",
                    description="Please provide an email for contact information.",
                    # True for autocomplete dropdowns with search functionality
                    search=False,
                    multiple=False,  # True for selecting multiple values
                    clearable=True,
                ),
            ),
        ],
    },
    {
        "section": "Data Asset Registration Tool - DART",
        "fields": [
            dict(
                field="imperial:dart_id",
                ui_widget="DART",
                template="dart_id.html",
                props=dict(
                    label="DART ID",
                    placeholder="Enter DART ID",
                    icon="address card outline",
                    # True for autocomplete dropdowns with search functionality
                    search=False,
                    multiple=False,  # True for selecting multiple values
                    clearable=True,
                ),
            ),
        ],
    },
]
