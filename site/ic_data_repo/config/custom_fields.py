"""Custom fields configuration, part of the settings."""

from invenio_records_resources.services.custom_fields import TextCF
from marshmallow import validate
from marshmallow_utils.fields import ISOLangString

RDM_NAMESPACES = {
    "imperial": "https://www.imperial.ac.uk",
}


class DartIDCF(TextCF):
    """Custom field for DART ID."""

    def __init__(self, name, **kwargs):
        """Initialize the custom field."""
        super().__init__(
            name,
            field_cls=str,
            field_args={
                "validate": validate.Length(min=1, max=100),
            },
            **kwargs,
        )

    @property
    def mapping(self):
        """Return the mapping for the custom field."""
        return {
            "properties": {
                "ID": {
                    "type": "text",
                },
            }
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
    DartIDCF(name="imperial:dart_id"),
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
        "section": "DART ID",
        "fields": [
            {
                "field": "imperial:dart_ids",
                "ui_widget": "DART",
                "template": "dart_id.html",
                "props": {
                    "label": ("imperial:dart_id"),
                    "ID": {
                        "label": ("DART ID"),
                        "placeholder": ("Add the title..."),
                        "description": ("Add the title of the experiment e.g ATLAS"),
                    },
                },
            }
        ],
    },
]
