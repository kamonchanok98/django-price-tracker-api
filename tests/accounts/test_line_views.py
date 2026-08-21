from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class LINELoginViewsTestCase(APITestCase):

    def setUp(self):
        # Update these URL names if yours differ in urls.py
        try:
            self.login_url = reverse("accounts:line-login-url")
            self.callback_url = reverse("accounts:line-callback")
        except Exception:
            # Fallback to direct path strings if URL names are not configured
            self.login_url = "/api/accounts/line/login-url/"
            self.callback_url = "/api/accounts/line/callback/"

    # --- LINELoginURLView Tests ---

    def test_get_line_login_url_success(self):
        """GET request returns LINE authorization URL with expected parameters."""
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("auth_url", response.data)
        self.assertIn(
            "https://access.line.me/oauth2/v2.1/authorize", response.data["auth_url"]
        )

    # --- LINECallbackView Tests ---

    def test_line_callback_missing_code(self):
        """POST request without authorization code returns 400 Bad Request."""
        response = self.client.post(self.callback_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Authorization code is required")

    @patch("accounts.views.requests.post")
    def test_line_callback_token_exchange_failure(self, mock_post):
        """Returns error status if LINE token exchange API fails."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_grant"}
        mock_post.return_value = mock_response

        response = self.client.post(
            self.callback_url, {"code": "invalid_code"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Failed to obtain token from LINE")
        self.assertEqual(response.data["details"], {"error": "invalid_grant"})

    @patch("accounts.views.requests.get")
    @patch("accounts.views.requests.post")
    def test_line_callback_profile_fetch_failure(self, mock_post, mock_get):
        """Returns error status if LINE profile fetching API fails."""
        # Token exchange success
        mock_token_res = MagicMock()
        mock_token_res.status_code = 200
        mock_token_res.json.return_value = {"access_token": "mock_access_token"}
        mock_post.return_value = mock_token_res

        # Profile fetch failure
        mock_profile_res = MagicMock()
        mock_profile_res.status_code = 401
        mock_profile_res.json.return_value = {"error": "Unauthorized access token"}
        mock_get.return_value = mock_profile_res

        response = self.client.post(
            self.callback_url, {"code": "valid_code"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["error"], "Failed to fetch user profile from LINE"
        )

    @patch("accounts.views.requests.get")
    @patch("accounts.views.requests.post")
    def test_line_callback_new_user_creation_success(self, mock_post, mock_get):
        """Creates new Django User and UserProfile when LINE user logs in for the first time."""
        # 1. Mock LINE token endpoint
        mock_token_res = MagicMock()
        mock_token_res.status_code = 200
        mock_token_res.json.return_value = {"access_token": "mock_access_token"}
        mock_post.return_value = mock_token_res

        # 2. Mock LINE profile endpoint
        mock_profile_res = MagicMock()
        mock_profile_res.status_code = 200
        mock_profile_res.json.return_value = {
            "userId": "U1234567890abcdef",
            "displayName": "John Doe",
            "pictureUrl": "https://profile.line-scdn.net/avatar.jpg",
        }
        mock_get.return_value = mock_profile_res

        response = self.client.post(
            self.callback_url, {"code": "valid_code"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response tokens and user payload
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["line_display_name"], "John Doe")
        self.assertEqual(response.data["line_user_id"], "U1234567890abcdef")

        # Verify DB entries
        self.assertTrue(User.objects.filter(username="line_U1234567890a").exists())
        user = User.objects.get(line_user_id="U1234567890abcdef")
        self.assertEqual(user.picture_url, "https://profile.line-scdn.net/avatar.jpg")

    @patch("accounts.views.requests.get")
    @patch("accounts.views.requests.post")
    def test_line_callback_existing_user_login_success(self, mock_post, mock_get):
        """Logs in existing LINE user and updates profile picture if changed."""
        # Create pre-existing user
        existing_user = User.objects.create_user(
            username="line_U1234567890a",
            line_user_id="U1234567890abcdef",
            picture_url="https://old-avatar.jpg",
        )

        # Mock LINE responses
        mock_token_res = MagicMock()
        mock_token_res.status_code = 200
        mock_token_res.json.return_value = {"access_token": "mock_access_token"}
        mock_post.return_value = mock_token_res

        mock_profile_res = MagicMock()
        mock_profile_res.status_code = 200
        mock_profile_res.json.return_value = {
            "userId": "U1234567890abcdef",
            "displayName": "John Updated",
            "pictureUrl": "https://new-avatar.jpg",  # Changed picture
        }
        mock_get.return_value = mock_profile_res

        response = self.client.post(
            self.callback_url, {"code": "valid_code"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_id"], existing_user.id)

        # Confirm no duplicate users were created and picture was updated
        self.assertEqual(User.objects.count(), 1)
        existing_user.refresh_from_db()
        self.assertEqual(existing_user.picture_url, "https://new-avatar.jpg")
