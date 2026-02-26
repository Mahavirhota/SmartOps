from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import WorkflowViewSet

router = DefaultRouter()
router.register(r'', WorkflowViewSet, basename='workflow')

urlpatterns = router.urls
