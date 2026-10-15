"""Imperial College Data Repository Symplectic Service Permissions."""

from typing import ClassVar

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AuthenticatedUser, SystemProcess


class SymplecticPermissionPolicy(RecordPermissionPolicy):
    """Permission policy for Symplectic service."""

    can_read: ClassVar = [AuthenticatedUser(), SystemProcess()]
