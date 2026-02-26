"""
Organization serializers with membership management.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Membership, Organization

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for organization CRUD."""
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'slug', 'owner', 'is_active',
            'member_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('owner', 'slug', 'created_at', 'updated_at')

    def get_member_count(self, obj: Organization) -> int:
        return obj.memberships.filter(is_active=True).count()


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer for membership management."""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Membership
        fields = ('id', 'user', 'user_email', 'organization', 'role', 'joined_at', 'is_active')
        read_only_fields = ('id', 'joined_at')


class InviteMemberSerializer(serializers.Serializer):
    """Serializer for inviting new members."""
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(
        choices=Membership.Role.choices,
        default=Membership.Role.MEMBER,
    )
