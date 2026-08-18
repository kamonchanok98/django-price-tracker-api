from unittest.mock import MagicMock, patch
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from tracker.models import Product
from tracker.tasks import (
    scrape_all_products_periodic_task,
    scrape_single_product_task,
)


class CeleryTaskTestCase(TestCase):

    def setUp(self):
        # Create a test user to satisfy the foreign key constraint
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

        self.product1 = Product.objects.create(
            user=self.user,
            name="Laptop",
            url="https://example.com/laptop",
            target_price=999.00,
        )
        self.product2 = Product.objects.create(
            user=self.user,
            name="Headphones",
            url="https://example.com/headphones",
            target_price=150.00,
        )

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATE=True,
    )
    @patch("tracker.tasks.scrape_and_update_product")
    def test_scrape_single_product_task_success(self, mock_scrape):
        """Verify single product task calls scraper synchronously and succeeds."""
        result = scrape_single_product_task.delay(self.product1.id)

        # Verify underlying scraper was called with the correct instance
        mock_scrape.assert_called_once_with(self.product1)
        self.assertTrue(result.successful())

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATE=True,
    )
    @patch("tracker.tasks.scrape_single_product_task.retry")
    @patch("tracker.tasks.scrape_and_update_product")
    def test_scrape_single_product_task_retry_on_error(self, mock_scrape, mock_retry):
        """Verify task retries when scrape_and_update_product raises an exception."""
        # Simulate scraper failure
        mock_scrape.side_effect = Exception("Network Connection Error")
        mock_retry.side_effect = Exception("Retry Triggered")

        with self.assertRaises(Exception) as ctx:
            scrape_single_product_task(self.product1.id)

        self.assertIn("Retry Triggered", str(ctx.exception))
        mock_retry.assert_called_once()

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATE=True,
    )
    @patch("tracker.tasks.scrape_single_product_task.delay")
    def test_scrape_all_products_periodic_task(self, mock_single_task_delay):
        """Verify periodic task iterates through all products and queues individual tasks."""
        scrape_all_products_periodic_task.delay()

        # Should call .delay() once for each existing product
        self.assertEqual(mock_single_task_delay.call_count, 2)
        mock_single_task_delay.assert_any_call(self.product1.id)
        mock_single_task_delay.assert_any_call(self.product2.id)
