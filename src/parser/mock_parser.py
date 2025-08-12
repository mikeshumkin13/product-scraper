from __future__ import annotations
from typing import List, Iterable, Any
import re
import json
from bs4 import BeautifulSoup
from .base import Product


def _to_products(items: Iterable[Any], query: str) -> List[Product]:
    """Унифицируем список словарей в список Product, пропуская мусор."""
    out: List[Product] = []
    q = query.lower()
    for item in items:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            if q not in name.lower():
                continue
            url = (
                str(item.get("url", "https://example.com")).strip()
                or "https://example.com"
            )
            price = item.get("price", "Нет цены")
            out.append(Product(name=name, url=url, price=price))
        # если внезапно пришла строка — пропускаем
    return out


def parse_mock_json(json_data: Any, query: str) -> List[Product]:
    """
    Принимает либо: str (JSON-текст), либо уже распарсенный объект (list/ dict).
    Возвращает отфильтрованный список Product.
    """
    data: Any = json_data
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except Exception:
            return []

    if isinstance(data, dict):
        # допускаем формат {"items":[...]}
        if "items" in data and isinstance(data["items"], list):
            return _to_products(data["items"], query)
        # или одна карточка
        return _to_products([data], query)

    if isinstance(data, list):
        return _to_products(data, query)

    return []


def parse_mock_html(html: str, query: str) -> List[Product]:
    """
    «Грязный» HTML-парсер для моков разных сайтов.
    Ищет карточки по набору распространённых классов.
    """
    soup = BeautifulSoup(html, "html.parser")
    q = query.lower()
    products: List[Product] = []

    # Набор шаблонов для названия и цены
    name_selectors = [
        "a.product-name",
        "a.catalog-product__name",
        "a.ProductCardVertical__name",
        "div.tile-hover-target a",
        "a",
        "div.product-title a",
        "a.product-card__name",
    ]
    price_selectors = [
        "span.product-price",
        "span.product-buy__price",
        "span.ProductCardVerticalPrice__price-current",
        "div.ui-pdp-price__content span",
        "ins.price__lower-price",
        "span.price, span.price__lower-price",
    ]

    # Контейнеры карточек
    card_candidates = soup.select(
        "div.product-info, div.catalog-product, div.ProductCardVertical, "
        "article, div.product-card, div.tile-hover-target, div.ProductCardHorizontal__header"
    )
    if not card_candidates:
        card_candidates = soup.select("div, article")

    for node in card_candidates:
        name = None
        href = None
        for sel in name_selectors:
            el = node.select_one(sel)
            if el and el.get_text(strip=True):
                name = el.get_text(strip=True)
                href = el.get("href")
                break

        price_text = None
        for sel in price_selectors:
            el = node.select_one(sel)
            if el and el.get_text(strip=True):
                price_text = el.get_text(strip=True)
                break

        if not name or not price_text:
            continue

        if q not in name.lower():
            continue

        url = href or "#"
        if not url.startswith("http"):
            url = "https://example.com" + url

        # очистка цены
        digits = re.sub(r"[^\d]", "", price_text)
        price: int | str = int(digits) if digits.isdigit() else price_text

        products.append(Product(name=name, url=url, price=price))

    return products
