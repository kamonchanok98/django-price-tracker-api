from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RegisterViewTests(APITestCase):

    def setUp(self):
        self.register_url = reverse("accounts:register")
        self.user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
        }

    def test_register_user_success(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, self.user_data["username"])

    def test_register_user_missing_password(self):
        data = {"username": "newuser", "email": "newuser@example.com"}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_duplicate_username(self):
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email_registration_fails(self):
        """Ensure registering an existing email returns 400 Bad Request."""
        User.objects.create_user(
            username="newuser@example.com",
            email="newuser@example.com",
            password="Password123",
        )

        response = self.client.post(
            self.register_url, self.user_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
