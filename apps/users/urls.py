from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import (PasswordSuggestionView, ProfileView, RegisterView,
                    SwitchTenantView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='user_profile'),
    path('switch-tenant/', SwitchTenantView.as_view(), name='switch_tenant'),
    path('password-suggestion/', PasswordSuggestionView.as_view(), name='password_suggestion'),
]
