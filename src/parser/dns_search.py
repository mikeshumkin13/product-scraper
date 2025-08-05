import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re


class DNSSearchParser:
    BASE_URL = "https://www.dns-shop.ru"

    def search(self, query: str) -> List[Dict]:
        search_url = f"{self.BASE_URL}/search/?q=" + query.replace(" ", "+")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        products = []

        for item in soup.select(".catalog-product"):
            name_el = item.select_one(".catalog-product__name")
            price_el = item.select_one(".product-buy__price")

            if name_el and price_el:
                name = name_el.get_text(strip=True)
                url = self.BASE_URL + name_el.get("href")
                price = price_el.get_text(strip=True)

                products.append({
                    "name": name,
                    "url": url,
                    "price": price,
                })

        return products


