from rest_framework.routers import DefaultRouter

from .views import InvoiceViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = router.urls
