from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from tracker.models import PriceHistory, Product


class ProductAPITestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password123")

        self.client.force_authenticate(user=self.user1)

        self.product1 = Product.objects.create(
            user=self.user1,
            name="Wireless Headphones",
            url="https://example.com/headphones",
            target_price=Decimal("100.00"),
            current_price=Decimal("120.00"),
        )
        PriceHistory.objects.create(product=self.product1, price=Decimal("120.00"))

        self.product2 = Product.objects.create(
            user=self.user2,
            name="Mechanical Keyboard",
            url="https://example.com/keyboard",
            target_price=Decimal("80.00"),
        )

    def test_list_products_user_isolation(self):
        """Authenticated user receives only their own products."""
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Wireless Headphones")

    def test_create_product(self):
        """Authenticated user can create a product automatically assigned to them."""
        payload = {
            "name": "Smartwatch",
            "url": "https://example.com/watch",
            "target_price": "199.99",
        }
        response = self.client.post("/api/products/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.filter(user=self.user1).count(), 2)

    def test_get_product_price_history(self):
        """Fetches historical price data points for a specific product."""
        response = self.client.get(f"/api/products/{self.product1.id}/history/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(Decimal(response.data[0]["price"]), Decimal("120.00"))

    def test_cannot_access_other_user_product_history(self):
        """Returns 404 when attempting to access another user's product or history."""
        response = self.client.get(f"/api/products/{self.product2.id}/history/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
