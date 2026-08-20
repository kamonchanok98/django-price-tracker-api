import os
from urllib.parse import urlencode

import requests
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers import RegisterSerializer, UserProfileSerializer

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "auth"


class CustomTokenRefreshView(TokenRefreshView):
    throttle_scope = "auth"


class LINELoginURLView(APIView):
    permission_classes = [AllowAny]
    """Returns the authorization URL to redirect users to LINE Login."""

    def get(self, request):
        client_id = os.getenv("LINE_LOGIN_CHANNEL_ID")
        redirect_uri = os.getenv("LINE_LOGIN_REDIRECT_URI")

        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": "random_secure_state_string",  # Generate dynamically in production
            "scope": "profile openid",
            "bot_prompt": "aggressive",  # Prompts user to add Official Account as friend
        }

        auth_url = f"https://access.line.me/oauth2/v2.1/authorize?{urlencode(params)}"
        return Response({"auth_url": auth_url}, status=status.HTTP_200_OK)


class LINECallbackView(APIView):
    permission_classes = [AllowAny]
    """Exchanges authorization code for tokens, fetches LINE profile, and logs in user."""

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"error": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Exchange authorization code for LINE Access Token
        token_url = "https://api.line.me/oauth2/v2.1/token"
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": os.getenv("LINE_LOGIN_REDIRECT_URI"),
            "client_id": os.getenv("LINE_LOGIN_CHANNEL_ID"),
            "client_secret": os.getenv("LINE_LOGIN_CHANNEL_SECRET"),
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        token_res = requests.post(
            token_url, data=token_data, headers=headers, timeout=10
        )
        if token_res.status_code != 200:
            return Response(
                {
                    "error": "Failed to obtain token from LINE",
                    "details": token_res.json(),
                },
                status=token_res.status_code,
            )

        access_token = token_res.json().get("access_token")

        # 2. Fetch LINE Profile using access token
        profile_url = "https://api.line.me/v2/profile"
        profile_headers = {"Authorization": f"Bearer {access_token}"}
        profile_res = requests.get(profile_url, headers=profile_headers, timeout=10)

        if profile_res.status_code != 200:
            return Response(
                {"error": "Failed to fetch user profile from LINE"},
                status=profile_res.status_code,
            )

        line_profile = profile_res.json()
        line_user_id = line_profile.get("userId")
        display_name = line_profile.get("displayName")
        picture_url = line_profile.get("pictureUrl")

        # 3. Get or Create Django User linked to line_user_id
        user = User.objects.filter(line_user_id=line_user_id).first()

        if user:
            user.picture_url = picture_url  # Keep picture updated if LINE photo changes
            user.save()
        else:
            # Generate unique username
            username = f"line_{line_user_id[:12]}"

            # create_user without a password automatically sets an unusable password
            user = User.objects.create_user(
                username=username,
                email="",
                line_user_id=line_user_id,
                picture_url=picture_url,
            )
            user.set_unusable_password()  # Explicitly prevents standard password login
            user.save()

        # 4. Issue SimpleJWT Tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user_id": user.id,
                "username": user.username,
                "line_display_name": display_name,
                "line_user_id": line_user_id,
                "line_picture_url": picture_url,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_scope = "auth"


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
