"""
Organization Service Layer — Business logic for tenant management.
"""
from typing import Optional, List
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, Membership

User = get_user_model()


class OrganizationService:
    """Handles organization (tenant) creation, membership, and settings."""

    @staticmethod
    @transaction.atomic
    def create_organization(name: str, owner: 'User') -> Organization:
        """
        Create a new organization and set the creator as OWNER.
        
        This establishes a new tenant boundary. All resources created
        within this organization are automatically scoped to it.
        """
        org = Organization.objects.create(
            name=name,
            owner=owner,
        )
        Membership.objects.create(
            user=owner,
            organization=org,
            role=Membership.Role.OWNER,
        )
        return org

    @staticmethod
    @transaction.atomic
    def invite_member(
        organization: Organization,
        email: str,
        role: str = Membership.Role.MEMBER,
        invited_by: Optional['User'] = None,
    ) -> Membership:
        """
        Invite a user to the organization.
        Creates the membership record; the user must already exist.
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError(f"No user found with email: {email}")

        membership, created = Membership.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={'role': role},
        )

        if not created:
            raise ValueError("User is already a member of this organization.")

        # If user has no active tenant, set this one
        if not user.tenant:
            user.tenant = organization
            user.role = role
            user.save(update_fields=['tenant', 'role'])

        return membership

    @staticmethod
    def remove_member(
        organization: Organization,
        user: 'User',
    ) -> None:
        """Remove a user from the organization."""
        if organization.owner == user:
            raise ValueError("Cannot remove the organization owner.")

        Membership.objects.filter(
            user=user,
            organization=organization,
        ).delete()

        # If this was the user's active tenant, clear it
        if user.tenant == organization:
            # Switch to another org or set to None
            next_membership = Membership.objects.filter(
                user=user,
                is_active=True,
            ).first()
            user.tenant = next_membership.organization if next_membership else None
            user.save(update_fields=['tenant'])

    @staticmethod
    def get_members(organization: Organization) -> List['User']:
        """Get all active members of an organization."""
        return User.objects.filter(
            memberships__organization=organization,
            memberships__is_active=True,
        ).select_related('tenant')
