from django.core.management.base import BaseCommand
from tracker.models import Product
from tracker.scraper import scrape_and_update_product

class Command(BaseCommand):
    help = "Scrapes current prices for all tracked products."

    def handle(self, *args, **options):
        products = Product.objects.all()
        self.stdout.write(f"Scraping {products.count()} products...")

        for product in products:
            res = scrape_and_update_product(product)
            if res["success"]:
                self.stdout.write(
                    self.style.SUCCESS(f"[{product.name}] Updated price: ${res['price']}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"[{product.name}] Failed: {res['error']}")
                )