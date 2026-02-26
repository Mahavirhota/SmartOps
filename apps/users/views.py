"""
User views — thin controllers delegating to services.

Architecture Decision:
Views only handle HTTP concerns (request parsing, response formatting).
All business logic is in UserService, making it testable and reusable.
"""
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    PasswordSuggestionSerializer,
    SwitchTenantSerializer,
)
from .services import UserService
from .utils import generate_random_password


class RegisterView(generics.CreateAPIView):
    """Register a new user (optionally with an organization)."""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ProfileView(generics.RetrieveAPIView):
    """Get the authenticated user's profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class SwitchTenantView(views.APIView):
    """Switch the authenticated user's active tenant context."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SwitchTenantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = UserService.switch_tenant(
                user=request.user,
                organization_id=str(serializer.validated_data['organization_id']),
            )
            return Response(
                UserProfileSerializer(user).data,
                status=status.HTTP_200_OK,
            )
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )


class PasswordSuggestionView(views.APIView):
    """Generate a secure random password suggestion."""
    permission_classes = [AllowAny]
    serializer_class = PasswordSuggestionSerializer

    def get(self, request):
        length = int(request.query_params.get('length', 12))
        password = generate_random_password(length)
        serializer = PasswordSuggestionSerializer({'password': password, 'length': length})
        return Response(serializer.data)
