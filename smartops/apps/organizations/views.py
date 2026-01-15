from rest_framework import viewsets, permissions
from .models import Organization
from .serializers import OrganizationSerializer

class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or self.request.user.is_anonymous:
            return Organization.objects.none()
        return self.request.user.organizations.all()

    def perform_create(self, serializer):
        org = serializer.save(owner=self.request.user)
        org.members.add(self.request.user)
