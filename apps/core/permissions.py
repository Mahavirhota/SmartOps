"""
RBAC Permissions — Role-Based Access Control with hierarchy.

Architecture Decision:
Permissions are declarative and composable. The role hierarchy
(OWNER > ADMIN > MEMBER > VIEWER) means an OWNER automatically
has all ADMIN, MEMBER, and VIEWER permissions. This reduces
the number of permission checks and simplifies authorization logic.
"""
from rest_framework.permissions import BasePermission


class RoleBasedPermission(BasePermission):
    """
    Base RBAC permission class.
    
    Subclass and set `required_role` to enforce minimum role level.
    Uses the role hierarchy from the User model.
    """
    required_role = 'viewer'

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_role_level(self.required_role)


class IsOwner(RoleBasedPermission):
    """Only organization owners can access."""
    required_role = 'owner'


class IsAdmin(RoleBasedPermission):
    """Admins and owners can access."""
    required_role = 'admin'


class IsMember(RoleBasedPermission):
    """Members, admins, and owners can access."""
    required_role = 'member'


class IsViewer(RoleBasedPermission):
    """All authenticated users with any role can access."""
    required_role = 'viewer'


class TenantPermission(BasePermission):
    """
    Ensures the user has an active tenant context.
    Prevents access to tenant-scoped resources without a tenant.
    """
    message = "No active tenant context. Please set X-Tenant-ID header."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request, 'tenant') and request.tenant is not None


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: only the object owner can modify.
    Others get read-only access.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Check if the object has an owner field
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False
