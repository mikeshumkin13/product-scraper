import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import urllib.parse


def search_citilink(query: str) -> List[Dict]:
    base_url = "https://www.citilink.ru/search/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Connection": "keep-alive",
    }

    # ⏱ задержка перед запросом
    time.sleep(3)

    params = {"text": query}

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            raise Exception("🔒 Заблокировано Citilink: Too Many Requests (429)")
        else:
            raise

    soup = BeautifulSoup(response.text, "html.parser")
    products = []

    items = soup.select("div.ProductCardHorizontal__header")
    prices = soup.select("div.ProductCardHorizontal__price_current-price")

    for item, price_item in zip(items, prices):
        title_tag = item.select_one("a")
        if not title_tag:
            continue

        name = title_tag.text.strip()
        url = urllib.parse.urljoin("https://www.citilink.ru", title_tag["href"])
        price = price_item.text.strip()

        products.append({
            "name": name,
            "url": url,
            "price": price,
        })

    return products


