"""
User serializers with service-layer integration.
Views remain thin — serializers delegate to services for business logic.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.services import UserService

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration and profile display."""
    organization_name = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Create an organization during registration."
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password',
            'role', 'is_verified', 'organization_name',
        )
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 10},
            'role': {'read_only': True},
            'is_verified': {'read_only': True},
        }

    def create(self, validated_data: dict) -> User:
        """Delegate creation to service layer."""
        org_name = validated_data.pop('organization_name', None)
        return UserService.register_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            organization_name=org_name,
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only serializer for user profile display."""
    tenant_name = serializers.CharField(
        source='tenant.name',
        read_only=True,
        default=None,
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role',
            'is_verified', 'tenant_name', 'date_joined',
        )
        read_only_fields = fields


class PasswordSuggestionSerializer(serializers.Serializer):
    """Serializer for secure password generation endpoint."""
    length = serializers.IntegerField(
        required=False,
        default=12,
        min_value=8,
        max_value=64,
    )
    password = serializers.CharField(read_only=True)


class SwitchTenantSerializer(serializers.Serializer):
    """Serializer for tenant context switching."""
    organization_id = serializers.UUIDField(required=True)
