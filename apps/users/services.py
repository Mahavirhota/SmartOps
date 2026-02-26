"""
User Service Layer — Business logic separated from views.

Architecture Decision:
Views should be thin controllers. All business logic lives in services.
This makes logic testable independently of HTTP, reusable across
management commands, Celery tasks, and other entry points.
"""
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.organizations.models import Membership

User = get_user_model()


class UserService:
    """Handles user registration, role management, and tenant operations."""

    @staticmethod
    @transaction.atomic
    def register_user(
        email: str,
        username: str,
        password: str,
        organization_name: Optional[str] = None,
    ) -> User:
        """
        Register a new user and optionally create their organization.

        When an organization_name is provided, the user becomes the OWNER
        of a new tenant, establishing the multi-tenant foundation.
        """
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
        )

        if organization_name:
            from apps.organizations.services import OrganizationService
            org = OrganizationService.create_organization(
                name=organization_name,
                owner=user,
            )
            user.tenant = org
            user.role = User.Role.OWNER
            user.save(update_fields=['tenant', 'role'])

        # Dispatch domain event
        from apps.core.events.dispatcher import EventDispatcher
        EventDispatcher.dispatch('user_created', {
            'user_id': str(user.id),
            'email': user.email,
        })

        return user

    @staticmethod
    def update_role(user: User, new_role: str, changed_by: User) -> User:
        """
        Update a user's role with authorization check.
        Only users with higher role level can change roles.
        """
        if not changed_by.has_role_level(User.Role.ADMIN):
            raise PermissionError("Only admins and owners can change roles.")

        if not changed_by.has_role_level(new_role):
            raise PermissionError("Cannot assign a role higher than your own.")

        old_role = user.role
        user.role = new_role
        user.save(update_fields=['role'])

        # Dispatch audit event
        from apps.core.events.dispatcher import EventDispatcher
        EventDispatcher.dispatch('role_changed', {
            'user_id': str(user.id),
            'old_role': old_role,
            'new_role': new_role,
            'changed_by': str(changed_by.id),
        })

        return user

    @staticmethod
    def switch_tenant(user: User, organization_id: str) -> User:
        """Switch user's active tenant context."""
        try:
            membership = Membership.objects.get(
                user=user,
                organization_id=organization_id,
                is_active=True,
            )
        except Membership.DoesNotExist:
            raise PermissionError("User is not a member of this organization.")

        user.tenant_id = organization_id
        user.role = membership.role
        user.save(update_fields=['tenant', 'role'])
        return user
