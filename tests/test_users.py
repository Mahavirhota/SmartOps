"""
User API Tests — Unit tests for registration and authentication.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration endpoint."""

    def test_register_user_success(self, api_client):
        """Test successful user registration."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecureP@ss123',
        }
        response = api_client.post(reverse('register'), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == 'newuser@example.com'
        assert 'password' not in response.data

    def test_register_user_with_organization(self, api_client):
        """Test registration with simultaneous org creation."""
        data = {
            'username': 'orgowner',
            'email': 'owner@example.com',
            'password': 'SecureP@ss123',
            'organization_name': 'My Company',
        }
        response = api_client.post(reverse('register'), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_duplicate_email_fails(self, api_client, user):
        """Test that duplicate email registration fails."""
        data = {
            'username': 'another',
            'email': 'test@example.com',  # Already exists
            'password': 'SecureP@ss123',
        }
        response = api_client.post(reverse('register'), data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Test JWT authentication endpoints."""

    def test_login_success(self, api_client, user):
        """Test successful login returns JWT tokens."""
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
        }
        response = api_client.post(reverse('token_obtain_pair'), data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_wrong_password(self, api_client, user):
        """Test login with wrong password fails."""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword123',
        }
        response = api_client.post(reverse('token_obtain_pair'), data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile endpoint."""

    def test_get_profile_authenticated(self, authenticated_client):
        """Test authenticated user can get their profile."""
        response = authenticated_client.get(reverse('user_profile'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'

    def test_get_profile_unauthenticated(self, api_client):
        """Test unauthenticated access is denied."""
        response = api_client.get(reverse('user_profile'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
