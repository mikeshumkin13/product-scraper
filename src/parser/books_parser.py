import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re

from .base import BaseParser


class BooksParser(BaseParser):
    def fetch_page(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text

    def parse(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        products = []

        items = soup.select("article.product_pod")
        for item in items:
            title = item.h3.a["title"]
            relative_url = item.h3.a["href"].replace("../../../", "")
            link = "https://books.toscrape.com/catalogue/" + relative_url
            price_text = item.select_one(".price_color").text
            price = self._extract_price(price_text)

            products.append(
                {
                    "name": title,
                    "url": link,
                    "price": price,
                }
            )

        return products

    def _extract_price(self, price_str: str) -> float:
        match = re.search(r"[\d.]+", price_str)
        return float(match.group()) if match else 0.0
