# accounts/urls.py
from django.urls import path

from accounts.views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LINECallbackView,
    LINELoginURLView,
    RegisterView,
    UserProfileView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", UserProfileView.as_view(), name="user_profile"),
    # JWT Auth Endpoints
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    # LINE login
    path("auth/line/login/", LINELoginURLView.as_view(), name="line-login-url"),
    path("auth/line/callback/", LINECallbackView.as_view(), name="line-callback"),
]
