import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import urllib.parse


def search_ozon(query: str) -> List[Dict]:
    base_url = "https://www.ozon.ru/search/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }

    params = {"text": query}
    response = requests.get(base_url, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    products = []

    cards = soup.select("div.tsBodyL")
    for card in cards[:10]:
        title_tag = card.select_one("a.tsBodyL")
        price_tag = card.select_one("span.tsBodyMBold")

        if not title_tag or not price_tag:
            continue

        name = title_tag.text.strip()
        url = urllib.parse.urljoin("https://www.ozon.ru", title_tag["href"])
        price = price_tag.text.strip()

        products.append({
            "name": name,
            "url": url,
            "price": price,
        })

    return products


