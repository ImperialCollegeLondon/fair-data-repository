"""General purpose cross module code."""

from flask import current_app
from marshmallow import validate


def length_validator_factory(min_setting_name: str = "", max_setting_name: str = ""):
    """Create a validator that checks the length of a string against a config setting.

    Used in favour of the built-in `validate.Length` because the minimum length is
    defined in the config and not known at schema definition time.

    Args:
        min_setting_name (str): The name of the config setting for the minimum length.
        max_setting_name (str): The name of the config setting for the maximum length.
    """

    def _validator(value):
        if min_setting_name:
            min_length = current_app.config[min_setting_name]
            if len(value) < min_length:
                raise validate.ValidationError(
                    f"Field must be at least {min_length} characters long."
                )
        if max_setting_name:
            max_length = current_app.config[max_setting_name]
            if len(value) > max_length:
                raise validate.ValidationError(
                    f"Field must be at most {max_length} characters long."
                )

    return _validator
