"""
Organization API Tests — CRUD, membership, and tenant isolation tests.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, Membership

User = get_user_model()


@pytest.mark.django_db
class TestOrganizationCRUD:
    """Test organization CRUD operations."""

    def test_list_organizations(self, tenant_client, organization):
        """Test listing organizations returns user's orgs only."""
        response = tenant_client.get(reverse('organization-list'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_create_organization(self, authenticated_client):
        """Test creating a new organization."""
        data = {'name': 'New Organization'}
        response = authenticated_client.post(
            reverse('organization-list'), data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Organization'

    def test_retrieve_organization(self, tenant_client, organization):
        """Test retrieving a specific organization."""
        response = tenant_client.get(
            reverse('organization-detail', args=[organization.id])
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == organization.name


@pytest.mark.django_db
@pytest.mark.integration
class TestTenantIsolation:
    """Test multi-tenant data isolation."""

    def test_cross_tenant_access_denied(self, api_client, user, organization):
        """Test that users cannot access other tenants' data."""
        # Create another user + org
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='OtherP@ss123!',
        )
        other_org = Organization.objects.create(
            name='Other Org',
            owner=other_user,
        )
        Membership.objects.create(
            user=other_user,
            organization=other_org,
            role=Membership.Role.OWNER,
        )

        # Authenticate as first user, try to access other org
        api_client.force_authenticate(user=user)
        response = api_client.get(
            reverse('organization-detail', args=[other_org.id])
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestOrganizationMembers:
    """Test membership management."""

    def test_list_members(self, tenant_client, organization):
        """Test listing organization members."""
        response = tenant_client.get(
            reverse('organization-members', args=[organization.id])
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_invite_member(self, tenant_client, organization):
        """Test inviting a new member."""
        # Create a user to invite
        invitee = User.objects.create_user(
            username='invitee',
            email='invitee@example.com',
            password='InviteeP@ss123!',
        )
        data = {'email': 'invitee@example.com', 'role': 'member'}
        response = tenant_client.post(
            reverse('organization-invite', args=[organization.id]),
            data,
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
