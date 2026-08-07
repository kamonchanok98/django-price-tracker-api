import re
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from tracker.models import Product, PriceHistory

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def extract_price_from_html(html_content):
    """Extracts the first numeric price pattern found in the HTML."""
    soup = BeautifulSoup(html_content, "lxml")

    # Common HTML tags/classes for prices across e-commerce sites
    price_selectors = [
        {"class_": re.compile(r"price", re.I)},
        {"id": re.compile(r"price", re.I)},
        {"itemprop": "price"},
    ]

    raw_price_str = None
    for selector in price_selectors:
        element = soup.find(**selector)
        if element:
            raw_price_str = element.get_text()
            break

    if not raw_price_str:
        return None

    # Extract digits and decimals (e.g., "$1,299.99" -> "1299.99")
    clean_price = re.sub(r"[^\d.]", "", raw_price_str.replace(",", ""))
    try:
        return Decimal(clean_price)
    except Exception:
        return None

def scrape_and_update_product(product: Product):
    """Fetches product URL, updates price history, and checks target price."""
    try:
        response = requests.get(product.url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        price = extract_price_from_html(response.text)
        if price is not None:
            # Save new price entry to database
            history_entry = PriceHistory.objects.create(product=product, price=price)

            # Check if target price met
            is_target_met = product.target_price and price <= product.target_price
            return {
                "success": True,
                "price": price,
                "target_met": is_target_met
            }
        return {"success": False, "error": "Could not parse price from page"}

    except Exception as e:
        return {"success": False, "error": str(e)}