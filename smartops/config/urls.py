from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator

class CustomSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema

schema_view = get_schema_view(
   openapi.Info(
      title="SmartOps API",
      default_version='v1',
      description="API documentation for SmartOps SaaS",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   generator_class=CustomSchemaGenerator,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/swagger/', permanent=False)),
    path('api/users/', include('apps.users.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    # path('api/billing/', include('apps.billing.urls')),
    # path('api/notifications/', include('apps.notifications.urls')),

    # Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
