"""Imperial College Data Repository Symplectic Service Permissions."""

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, SystemProcess


class SymplecticPermissionPolicy(RecordPermissionPolicy):
    """Permission policy for Symplectic service."""

    can_read = [AuthenticatedUser(), SystemProcess()]
