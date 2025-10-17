"""Permission configuration."""

from flask_principal import ActionNeed
from invenio_rdm_records.services.permissions import RDMRecordPermissionPolicy
from invenio_records_permissions.generators import Generator, SystemProcess
from invenio_records_resources.services.files.generators import IfTransferType

from .link_only_transfer import LINK_ONLY_TRANSFER_TYPE

ALLOWED_JOB_FAMILIES = [
    "Academic & Research",
    "Honorary Academics",
    "Clinical Research",
    "Clinical Academic",
    "Visiting Researcher",
]
"""The job families that are allowed to deposit datasets."""

POSTGRADUATE_ROLE_TYPE = "Research Postgraduate"
"""The role types that are allowed to deposit datasets."""


deposit_action = ActionNeed("deposit-action")
"""Action representing the ability to deposit datasets."""


class AbleToDeposit(Generator):
    """Permission generator for dataset deposit."""

    def needs(self, **kwargs):
        """The needs associated with the dataset deposit permission."""
        return [deposit_action]


deposit_link_only_action = ActionNeed("deposit-link-only-action")
"""Action representing the ability to deposit link-only records."""


class AbleToDepositLinkOnly(Generator):
    """Permission generator for link-only dataset deposit."""

    def needs(self, **kwargs):
        """The needs associated with the link-only deposit permission."""
        return [deposit_link_only_action]


class ImperialRecordPermissionPolicy(RDMRecordPermissionPolicy):
    """The permission policy for the repository.

    A lightly customised version of the standard InvenioRDM permission policy.
    Implements additional restrictions on depositing datasets.
    """

    can_create = [AbleToDeposit(), SystemProcess()]

    can_draft_create_files = RDMRecordPermissionPolicy.can_draft_create_files + [
        IfTransferType(
            LINK_ONLY_TRANSFER_TYPE,
            [AbleToDepositLinkOnly()],
        )
    ]

    can_draft_get_content_files = (
        RDMRecordPermissionPolicy.can_draft_get_content_files
        + [
            IfTransferType(
                LINK_ONLY_TRANSFER_TYPE,
                [AbleToDepositLinkOnly()],
            )
        ]
    )

    can_get_content_files = RDMRecordPermissionPolicy.can_get_content_files + [
        IfTransferType(
            LINK_ONLY_TRANSFER_TYPE,
            [AbleToDepositLinkOnly()],
        )
    ]


def user_is_postgraduate(role_type: str, job_family: str | None) -> bool:
    """Checks if a user is a postgraduate."""
    if role_type == POSTGRADUATE_ROLE_TYPE:
        if job_family is not None:
            raise ValueError("Unexpected combination of role type and job family.")
        return True
    return False


def user_is_allowed_employee(role_type: str, job_family: str | None) -> bool:
    """Checks if a user has an allowed job family."""
    if job_family in ALLOWED_JOB_FAMILIES:
        if role_type == POSTGRADUATE_ROLE_TYPE:
            raise ValueError("Unexpected combination of role type and job family.")
        return True
    return False


def can_user_deposit(role_type: str, job_family: str | None) -> bool:
    """Checks if a user can deposit datasets based on their identity data."""
    if user_is_postgraduate(role_type, job_family) or user_is_allowed_employee(
        role_type, job_family
    ):
        return True
    return False
