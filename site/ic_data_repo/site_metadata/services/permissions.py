"""Site Metadata permissions."""

from invenio_records_permissions import BasePermissionPolicy
from invenio_records_permissions.generators import AnyUser, SystemProcess


class SiteMetadataPermissionPolicy(BasePermissionPolicy):
    """Site Metadata permission policy."""

    can_upload_validate = [AnyUser(), SystemProcess()]
    can_index_on_publish = [SystemProcess()]
