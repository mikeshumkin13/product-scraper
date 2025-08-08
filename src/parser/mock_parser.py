from typing import List
import re
from bs4 import BeautifulSoup
from parser.base import Product
import json
from pathlib import Path



def parse_mock_html(site: str, query: str) -> List[Product]:
    """
    Парсит HTML-файл с мок-данными для указанного сайта и фильтрует товары по запросу.

    :param site: Название сайта (dns, citilink, ozon)
    :param query: Поисковый запрос
    :return: Список продуктов
    """
    mock_path = Path(f"src/parser/mock/{site}_mock.html")
    if not mock_path.exists():
        return []

    with open(mock_path, encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    query_lower = query.lower()
    products = []

    if site == "dns":
        cards = soup.select("div.product-info")
        for card in cards:
            name_tag = card.select_one("a.product-name")
            price_tag = card.select_one("span.product-price")
            if name_tag and price_tag and query_lower in name_tag.text.lower():
                url = "https://dns-shop.ru" + name_tag["href"]
                price = int(price_tag.text.replace("₽", "").replace(" ", ""))
                products.append(Product(name=name_tag.text.strip(), url=url, price=price))

    elif site == "citilink":
        names = soup.select("div.ProductCardHorizontal__header > a")
        prices = soup.select("div.ProductCardHorizontal__price_current-price")
        for name_tag, price_tag in zip(names, prices):
            if query_lower in name_tag.text.lower():
                url = "https://citilink.ru" + name_tag["href"]
                price = int(price_tag.text.replace("₽", "").replace(" ", ""))
                products.append(Product(name=name_tag.text.strip(), url=url, price=price))

    elif site == "ozon":
        names = soup.select("div.tile-hover-target > a")
        prices = soup.select("div.ui-pdp-price__content > span")
        for name_tag, price_tag in zip(names, prices):
            if query_lower in name_tag.text.lower():
                url = "https://ozon.ru" + name_tag["href"]
                price = int(price_tag.text.replace("₽", "").replace(" ", ""))
                products.append(Product(name=name_tag.text.strip(), url=url, price=price))

    return products


def parse_mock_json(data: List[dict], query: str) -> List[Product]:
    """
    Парсит JSON-данные (список словарей) и фильтрует товары по запросу.

    :param data: Список словарей с товарами
    :param query: Поисковый запрос
    :return: Список объектов Product
    """
    query_lower = query.lower()
    products = []

    for item in data:
        name = item.get("name", "")
        if query_lower in name.lower():
            url = item.get("url", "https://example.com")
            price = item.get("price", 0)
            products.append(Product(name=name, url=url, price=price))

    return products

