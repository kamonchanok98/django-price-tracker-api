from django.contrib.auth import get_user_model
from django.test import TestCase

from tracker.models import PriceHistory, Product

User = get_user_model()


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.product = Product.objects.create(
            user=self.user,
            name="Test Product",
            url="http://example.com/product",
            target_price=100.00,
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), "Test Product")

    def test_price_history_str(self):
        price_history = PriceHistory.objects.create(product=self.product, price=99.99)
        expected_str = f"Test Product - $99.99 at {price_history.recorded_at.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(price_history), expected_str)
