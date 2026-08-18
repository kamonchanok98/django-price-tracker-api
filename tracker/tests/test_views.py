from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from tracker.models import PriceHistory, Product

# Patch location matching where scrape_and_update_product is imported in views.py
PATCH_SCRAPE = "tracker.views.scrape_and_update_product"


class ProductViewSetTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password123")

        self.product1 = Product.objects.create(
            user=self.user1,
            name="Wireless Mouse",
            url="https://example.com/mouse",
            target_price=Decimal("20.00"),
        )
        self.product2 = Product.objects.create(
            user=self.user2,
            name="Mechanical Keyboard",
            url="https://example.com/keyboard",
            target_price=Decimal("50.00"),
        )

    def test_unauthenticated_access_denied(self):
        """Ensures unauthenticated requests return 401 Unauthorized."""
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_queryset_user_isolation(self):
        """Ensures users can only list their own tracked products."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Safely handle both paginated (dict) and non-paginated (list) responses
        results = (
            response.data["results"]
            if isinstance(response.data, dict)
            else response.data
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.product1.id)

    def test_perform_create_assigns_authenticated_user(self):
        """Ensures perform_create automatically sets request.user as owner."""
        self.client.force_authenticate(user=self.user1)
        payload = {
            "name": "Gaming Monitor",
            "url": "https://example.com/monitor",
            "target_price": "299.99",
        }
        response = self.client.post("/api/products/", payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Gaming Monitor")

        # Verify database record owner
        created_product = Product.objects.get(id=response.data["id"])
        self.assertEqual(created_product.user, self.user1)

    def test_retrieve_own_product(self):
        """Allows user to retrieve their own product detail."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/products/{self.product1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_other_user_product_returns_404(self):
        """Prevents access to another user's product by returning 404."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/products/{self.product2.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch(PATCH_SCRAPE)
    def test_trigger_scrape_success(self, mock_scrape):
        """Tests the POST /api/products/{id}/scrape/ endpoint on successful scrape."""
        mock_scrape.return_value = {
            "success": True,
            "price": Decimal("18.50"),
            "target_met": True,
        }

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f"/api/products/{self.product1.id}/scrape/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Price updated successfully")
        self.assertEqual(response.data["current_price"], "18.50")
        self.assertTrue(response.data["target_met"])

    @patch(PATCH_SCRAPE)
    def test_trigger_scrape_failure(self, mock_scrape):
        """Tests the POST /api/products/{id}/scrape/ endpoint on scrape error."""
        mock_scrape.return_value = {
            "success": False,
            "error": "Could not parse price from page",
        }

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f"/api/products/{self.product1.id}/scrape/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Could not parse price from page")


class PriceHistoryViewSetTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password123")
        self.user2 = User.objects.create_user(username="user2", password="password123")

        self.product1 = Product.objects.create(
            user=self.user1, name="Mouse", url="https://example.com/mouse"
        )
        self.product2 = Product.objects.create(
            user=self.user2, name="Keyboard", url="https://example.com/keyboard"
        )

        self.history1 = PriceHistory.objects.create(
            product=self.product1, price=Decimal("25.00")
        )
        self.history2 = PriceHistory.objects.create(
            product=self.product2, price=Decimal("60.00")
        )

    def test_unauthenticated_access_denied(self):
        """Ensures unauthenticated requests to price history return 401."""
        response = self.client.get("/api/price-history/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_queryset_filters_by_user_products(self):
        """Ensures users only see price histories for their own products."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/price-history/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Safely handle both paginated (dict) and non-paginated (list) responses
        results = (
            response.data["results"]
            if isinstance(response.data, dict)
            else response.data
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.history1.id)

    def test_retrieve_own_price_history(self):
        """Allows user to retrieve price history belonging to their product."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/price-history/{self.history1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_other_user_price_history_returns_404(self):
        """Prevents viewing price history belonging to another user's product."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/price-history/{self.history2.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
