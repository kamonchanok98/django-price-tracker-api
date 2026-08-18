from celery import shared_task
from tracker.models import Product
from tracker.scraper import scrape_and_update_product


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_single_product_task(self, product_id):
    try:
        product = Product.objects.get(id=product_id)
        scrape_and_update_product(product)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def scrape_all_products_periodic_task():
    product_ids = Product.objects.values_list("id", flat=True)
    for p_id in product_ids:
        scrape_single_product_task.delay(p_id)
