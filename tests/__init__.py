"""
Shared test fixtures for SmartOps test suite.
Provides pre-configured API client, users, organizations, and tenants.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organizations.models import Membership, Organization

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def user(db) -> User:
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPassword123!',
    )


@pytest.fixture
def admin_user(db) -> User:
    """Create a test admin user."""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='AdminPassword123!',
        role=User.Role.ADMIN,
    )


@pytest.fixture
def organization(db, user) -> Organization:
    """Create a test organization with the user as owner."""
    org = Organization.objects.create(
        name='Test Organization',
        owner=user,
    )
    Membership.objects.create(
        user=user,
        organization=org,
        role=Membership.Role.OWNER,
    )
    user.tenant = org
    user.role = User.Role.OWNER
    user.save()
    return org


@pytest.fixture
def authenticated_client(api_client, user) -> APIClient:
    """Authenticated DRF test client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def tenant_client(api_client, user, organization) -> APIClient:
    """Authenticated client with active tenant context."""
    api_client.force_authenticate(user=user)
    api_client.credentials(HTTP_X_TENANT_ID=str(organization.id))
    return api_client
