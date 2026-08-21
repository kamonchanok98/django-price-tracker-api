from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class TokenObtainViewTests(APITestCase):

    def setUp(self):
        self.token_obtain_url = reverse("accounts:token_obtain_pair")
        self.token_refresh_url = reverse("accounts:token_refresh")
        self.username = "tokenuser"
        self.password = "StrongPassword123!"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )

    def test_obtain_token_pair_success(self):
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.token_obtain_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_pair_invalid_credentials(self):
        data = {"username": self.username, "password": "WrongPassword"}
        response = self.client.post(self.token_obtain_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_success(self):
        obtain_resp = self.client.post(
            self.token_obtain_url,
            {"username": self.username, "password": self.password},
        )
        refresh_token = obtain_resp.data["refresh"]

        response = self.client.post(self.token_refresh_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
