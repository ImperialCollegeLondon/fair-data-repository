"""Permission configuration."""

from typing import ClassVar

from flask_principal import ActionNeed
from invenio_rdm_records.services.permissions import RDMRecordPermissionPolicy
from invenio_records_permissions.generators import Generator, SystemProcess

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

deposit_description_action = ActionNeed("deposit-description-action")
"""Action representing the ability to deposit datasets with a description."""

restricted_license_action = ActionNeed("restricted-license-action")
"""Action representing the ability to select a restricted licence."""


class AbleToDeposit(Generator):
    """Permission generator for dataset deposit."""

    def needs(self, **kwargs):
        """The needs associated with the dataset deposit permission."""
        return [deposit_action]


class AbleToDepositDescription(Generator):
    """Permission generator for dataset deposit with description."""

    def needs(self, **kwargs):
        """The needs associated with the dataset deposit permission."""
        return [deposit_description_action]


class AbleToSelectRestrictedLicense(Generator):
    """Permission generator for selecting a restricted licence."""

    def needs(self, **kwargs):
        """The needs associated with restricted licence selection."""
        return [restricted_license_action]


class ImperialRecordPermissionPolicy(RDMRecordPermissionPolicy):
    """The permission policy for the repository.

    A lightly customised version of the standard InvenioRDM permission policy.
    Implements additional restrictions on depositing datasets.
    """

    can_create: ClassVar = [AbleToDeposit(), SystemProcess()]
    can_select_restricted_license: ClassVar = [
        AbleToSelectRestrictedLicense(),
        SystemProcess(),
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
