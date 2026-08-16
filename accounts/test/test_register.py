from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class RegisterAPITests(APITestCase):
    def setUp(self):
        # 'register' matches the path name in accounts/urls.py
        self.register_url = reverse("register")
        self.valid_payload = {
            "email": "newuser@example.com",
            "password": "SecurePassword123",
        }

    def test_successful_registration(self):
        """Ensure a user can register with valid email and password."""
        response = self.client.post(
            self.register_url, self.valid_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, "newuser@example.com")
        # Security check: Password should never be returned in response body
        self.assertNotIn("password", response.data)

    def test_duplicate_email_registration_fails(self):
        """Ensure registering an existing email returns 400 Bad Request."""
        User.objects.create_user(
            username="newuser@example.com",
            email="newuser@example.com",
            password="Password123",
        )

        response = self.client.post(
            self.register_url, self.valid_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_missing_password_fails(self):
        """Ensure registration fails when password is missing."""
        payload = {"email": "incomplete@example.com"}
        response = self.client.post(self.register_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
