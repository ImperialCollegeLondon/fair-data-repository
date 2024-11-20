"""Custom fields configuration, part of the settings."""

from invenio_records_resources.services.custom_fields import TextCF
from marshmallow import validate
from marshmallow_utils.fields import ISOLangString

RDM_NAMESPACES = {
    "imperial": "https://www.imperial.ac.uk",
}

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
            )
        ],
    }
]
