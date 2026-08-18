from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class UserProfileViewTests(APITestCase):

    def setUp(self):
        self.profile_url = reverse('accounts:user_profile')
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='StrongPassword123!',
        )

    def test_get_profile_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_update_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        update_data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'updated@example.com',
        }
        response = self.client.patch(self.profile_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.email, 'updated@example.com')