from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from apps.core.views.health import HealthCheckView


class CustomSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title="SmartOps API",
        default_version='v1',
        description=(
            "Production-grade SaaS API for SmartOps.\n\n"
            "## Authentication\n"
            "All endpoints require JWT Bearer token authentication.\n"
            "Obtain a token at `POST /api/users/login/`.\n\n"
            "## Multi-Tenancy\n"
            "Set `X-Tenant-ID` header to switch organization context."
        ),
        contact=openapi.Contact(email="support@smartops.io"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    generator_class=CustomSchemaGenerator,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Root redirect
    path('', RedirectView.as_view(url='/swagger/', permanent=False)),

    # DRF API Auth (for Swagger 'Django Login' button)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # API endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/workflows/', include('apps.workflows.urls')),
    path('api/billing/', include('apps.billing.urls')),
    path('api/notifications/', include('apps.notifications.urls')),

    # Health & Monitoring
    path('health/', HealthCheckView.as_view(), name='health'),
    path('', include('django_prometheus.urls')),

    # Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
