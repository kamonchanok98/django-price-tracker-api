from decimal import Decimal
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

# Update import path to match your actual file location
from tracker.scraper import send_line_alert


class SendLineAlertTestCase(TestCase):

    def setUp(self):
        # Create a mock product object structure
        self.mock_product = MagicMock()
        self.mock_product.name = "Wireless Headphones"
        self.mock_product.target_price = Decimal("100.00")
        self.mock_product.url = "https://example.com/item"
        self.mock_product.user.profile.line_user_id = "U1234567890abcdef"

    @patch("os.getenv")
    @patch("tracker.scraper.requests.post")  # Patch requests inside your module
    def test_send_line_alert_success(self, mock_post, mock_getenv):
        """Sends LINE push alert successfully with correct headers and payload."""
        mock_getenv.return_value = "mock_channel_access_token"

        # Mock HTTP 200 response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        send_line_alert(self.mock_product, Decimal("85.00"))

        # 1. Assert requests.post was called once
        mock_post.assert_called_once()

        # 2. Assert payload and headers
        _, kwargs = mock_post.call_args
        self.assertEqual(
            kwargs["headers"]["Authorization"], "Bearer mock_channel_access_token"
        )
        self.assertEqual(kwargs["json"]["to"], "U1234567890abcdef")

        # Check alert message contents
        message_text = kwargs["json"]["messages"][0]["text"]
        self.assertIn("🚨 Price Drop Alert!", message_text)
        self.assertIn("Wireless Headphones", message_text)
        self.assertIn("Current Price: $85.00", message_text)

    @patch("os.getenv")
    @patch("tracker.scraper.requests.post")
    def test_send_line_alert_missing_token(self, mock_post, mock_getenv):
        """Skipped when LINE_CHANNEL_ACCESS_TOKEN env variable is missing."""
        mock_getenv.return_value = None  # No token configured

        send_line_alert(self.mock_product, Decimal("85.00"))

        # Should return early without sending an HTTP request
        mock_post.assert_not_called()

    @patch("os.getenv")
    @patch("tracker.scraper.requests.post")
    def test_send_line_alert_missing_line_user_id(self, mock_post, mock_getenv):
        """Skipped when the user profile does not have a LINE user ID."""
        mock_getenv.return_value = "mock_channel_access_token"
        self.mock_product.user.profile.line_user_id = None  # User hasn't linked LINE

        send_line_alert(self.mock_product, Decimal("85.00"))

        # Should return early without sending an HTTP request
        mock_post.assert_not_called()

    @patch("os.getenv")
    @patch("tracker.scraper.requests.post")
    def test_send_line_alert_request_exception(self, mock_post, mock_getenv):
        """Catches requests.RequestException gracefully without raising an unhandled exception."""
        mock_getenv.return_value = "mock_channel_access_token"

        # Simulate an API network error or HTTP 500
        mock_post.side_effect = requests.RequestException(
            "Connection error to LINE server"
        )

        # Function should catch error and print failure without crashing
        try:
            send_line_alert(self.mock_product, Decimal("85.00"))
        except requests.RequestException:
            self.fail("send_line_alert raised RequestException unexpectedly!")
