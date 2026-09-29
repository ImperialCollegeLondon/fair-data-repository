"""Local file transfer provider with optional description."""

from invenio_records_resources.services.files.transfer.providers.local import (
    LocalTransfer,
)
from marshmallow import fields, validate

DESCRIPTION_TRANSFER_TYPE = "D"
"""Identifier for description transfer type."""


class DescriptionTransferSchema(LocalTransfer.Schema):
    """Schema for description transfer type."""

    description = fields.String(required=False, validate=validate.Length(max=100))
    """Optional description field for the transfer."""


class DescriptionTransfer(LocalTransfer):
    """Local transfer with optional description."""

    transfer_type = DESCRIPTION_TRANSFER_TYPE

    Schema = DescriptionTransferSchema
