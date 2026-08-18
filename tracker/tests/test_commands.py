from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from tracker.models import Product

COMMAND_MODULE_PATCH = (
    "tracker.management.commands.scrape_prices.scrape_and_update_product"
)


class ScrapeProductsCommandTest(TestCase):
    def setUp(self):
        # Create a test user for foreign key constraints
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

        # Pass user and url during product creation
        self.product_success = Product.objects.create(
            user=self.user, name="Wireless Mouse", url="https://example.com/mouse"
        )
        self.product_fail = Product.objects.create(
            user=self.user, name="Gaming Keyboard", url="https://example.com/keyboard"
        )

    @patch(COMMAND_MODULE_PATCH)
    def test_handle_success_and_failure_branches(self, mock_scrape):
        """Tests that both success and error branches execute and print expected stdout."""

        def side_effect(product):
            if product.id == self.product_success.id:
                return {"success": True, "price": 29.99}
            return {"success": False, "error": "HTTP 404 Not Found"}

        mock_scrape.side_effect = side_effect

        out = StringIO()
        call_command("scrape_prices", stdout=out)

        output = out.getvalue()

        self.assertIn("Scraping 2 products...", output)
        self.assertIn("[Wireless Mouse] Updated price: $29.99", output)
        self.assertIn("[Gaming Keyboard] Failed: HTTP 404 Not Found", output)
        self.assertEqual(mock_scrape.call_count, 2)

    @patch(COMMAND_MODULE_PATCH)
    def test_handle_empty_database(self, mock_scrape):
        """Tests command execution when no products exist in the database."""
        Product.objects.all().delete()

        out = StringIO()
        call_command("scrape_prices", stdout=out)

        output = out.getvalue()

        self.assertIn("Scraping 0 products...", output)
        mock_scrape.assert_not_called()
