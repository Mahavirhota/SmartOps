"""
Organization views — thin controllers with tenant-aware querysets.
Uses select_related/prefetch_related to prevent N+1 queries.
"""
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Membership, Organization
from .serializers import (InviteMemberSerializer, MembershipSerializer,
                          OrganizationSerializer)
from .services import OrganizationService


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    CRUD for organizations.

    Lists only organizations the authenticated user belongs to.
    N+1 prevention: uses select_related for owner FK.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or self.request.user.is_anonymous:
            return Organization.objects.none()
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
        ).select_related('owner').distinct()

    def perform_create(self, serializer):
        """Delegate to service layer for org creation."""
        org = OrganizationService.create_organization(
            name=serializer.validated_data['name'],
            owner=self.request.user,
        )
        serializer.instance = org

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List all members of an organization."""
        org = self.get_object()
        memberships = Membership.objects.filter(
            organization=org,
            is_active=True,
        ).select_related('user')
        serializer = MembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        """Invite a user to the organization."""
        org = self.get_object()
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            membership = OrganizationService.invite_member(
                organization=org,
                email=serializer.validated_data['email'],
                role=serializer.validated_data.get('role', Membership.Role.MEMBER),
                invited_by=request.user,
            )
            return Response(
                MembershipSerializer(membership).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
