from decimal import Decimal
from unittest.mock import MagicMock, patch
import requests

from django.contrib.auth.models import User
from django.test import TestCase

from tracker.models import PriceHistory, Product
from tracker.scraper import extract_price_from_html, scrape_and_update_product


class ScraperTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.product = Product.objects.create(
            user=self.user,
            name="Wireless Headphones",
            url="https://example.com/headphones",
            target_price=Decimal("100.00"),
        )

    # =========================================================================
    # Tests for extract_price_from_html()
    # =========================================================================

    def test_extract_price_class_selector(self):
        """Extracts price successfully using the class attribute selector."""
        html = '<div class="product-price-display">$1,299.99</div>'
        price = extract_price_from_html(html)
        self.assertEqual(price, Decimal("1299.99"))

    def test_extract_price_id_selector(self):
        """Extracts price successfully using the id attribute selector."""
        html = '<span id="item-price">$49.50</span>'
        price = extract_price_from_html(html)
        self.assertEqual(price, Decimal("49.50"))

    def test_extract_price_itemprop_selector(self):
        """Extracts price successfully using the itemprop attribute selector."""
        html = '<span itemprop="price">75.00</span>'
        price = extract_price_from_html(html)
        self.assertEqual(price, Decimal("75.00"))

    def test_extract_price_no_matching_element(self):
        """Returns None when no price selector exists in HTML."""
        html = "<div><p>Out of stock, check back later.</p></div>"
        price = extract_price_from_html(html)
        self.assertIsNone(price)

    def test_extract_price_invalid_decimal_conversion(self):
        """Returns None when matching tag contains text with no valid numeric digits."""
        html = '<div class="price">Currently Unavailable</div>'
        price = extract_price_from_html(html)
        self.assertIsNone(price)

    # =========================================================================
    # Tests for scrape_and_update_product()
    # =========================================================================

    @patch("tracker.scraper.requests.get")
    def test_scrape_success_target_price_met(self, mock_get):
        """Successfully updates product price history when target price is met."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<div class="price">$89.99</div>'
        mock_get.return_value = mock_response

        result = scrape_and_update_product(self.product)

        self.assertTrue(result["success"])
        self.assertEqual(result["price"], Decimal("89.99"))
        self.assertTrue(result["target_met"])
        self.assertEqual(PriceHistory.objects.filter(product=self.product).count(), 1)

    @patch("tracker.scraper.requests.get")
    def test_scrape_success_target_price_not_met(self, mock_get):
        """Successfully updates product price history when price exceeds target."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<div class="price">$150.00</div>'
        mock_get.return_value = mock_response

        result = scrape_and_update_product(self.product)

        self.assertTrue(result["success"])
        self.assertEqual(result["price"], Decimal("150.00"))
        self.assertFalse(result["target_met"])
        self.assertEqual(PriceHistory.objects.filter(product=self.product).count(), 1)

    @patch("tracker.scraper.requests.get")
    def test_scrape_success_without_target_price(self, mock_get):
        """Handles products that do not have a target price configured."""
        self.product.target_price = None
        self.product.save()

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<div class="price">$50.00</div>'
        mock_get.return_value = mock_response

        result = scrape_and_update_product(self.product)

        self.assertTrue(result["success"])
        self.assertEqual(result["price"], Decimal("50.00"))
        self.assertFalse(bool(result["target_met"]))

    @patch("tracker.scraper.requests.get")
    def test_scrape_unparseable_price_error(self, mock_get):
        """Returns error result when HTML lacks price data without saving history."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "<html><body>No prices here</body></html>"
        mock_get.return_value = mock_response

        result = scrape_and_update_product(self.product)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Could not parse price from page")
        self.assertEqual(PriceHistory.objects.filter(product=self.product).count(), 0)

    @patch("tracker.scraper.requests.get")
    def test_scrape_http_request_exception(self, mock_get):
        """Catches request network failures gracefully."""
        mock_get.side_effect = requests.RequestException("Connection timed out")

        result = scrape_and_update_product(self.product)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Connection timed out")
        self.assertEqual(PriceHistory.objects.filter(product=self.product).count(), 0)
