from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class LoginAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="Password123",
        )
        self.login_url = reverse("token_obtain_pair")  # SimpleJWT login URL

    def test_successful_login(self):
        payload = {"username": "user@example.com", "password": "Password123"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
