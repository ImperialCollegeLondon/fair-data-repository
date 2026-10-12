"""Local file transfer provider with optional description."""

from invenio_records_resources.services.files.transfer.providers.local import (
    LocalTransfer,
)
from marshmallow import fields

from .utils import length_validator_factory

DESCRIPTION_TRANSFER_TYPE = "D"
"""Identifier for description transfer type."""


class DescriptionTransferSchema(LocalTransfer.Schema):
    """Schema for description transfer type."""

    description = fields.String(
        required=False,
        validate=length_validator_factory(
            max_setting_name="FILE_DESCRIPTION_MAX_LENGTH"
        ),
    )
    """Optional description field for the transfer."""


class DescriptionTransfer(LocalTransfer):
    """Local transfer with optional description."""

    transfer_type = DESCRIPTION_TRANSFER_TYPE

    Schema = DescriptionTransferSchema
