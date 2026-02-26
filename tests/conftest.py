"""
Shared test fixtures for SmartOps test suite.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organizations.models import Membership, Organization

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPassword123!',
    )


@pytest.fixture
def organization(db, user) -> Organization:
    org = Organization.objects.create(name='Test Org', owner=user)
    Membership.objects.create(user=user, organization=org, role=Membership.Role.OWNER)
    user.tenant = org
    user.role = User.Role.OWNER
    user.save()
    return org


@pytest.fixture
def authenticated_client(api_client, user) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def tenant_client(api_client, user, organization) -> APIClient:
    api_client.force_authenticate(user=user)
    api_client.credentials(HTTP_X_TENANT_ID=str(organization.id))
    return api_client
