import json
import time
from selenium.webdriver.common.by import By
from utils.selenium_driver import get_selenium_driver
from .base import Product
from pathlib import Path
from bs4 import BeautifulSoup





def search_wildberries(query: str, mode: str = "real") -> list[Product]:
    """
       Парсит Wildberries в реальном режиме через Selenium или заглушки (mock).

       Args:
           query (str): Поисковый запрос.
           mode (str): Режим работы: 'real' (по умолчанию) или 'mock'.

       Returns:
           list[Product]: Список найденных товаров.
       """

    if mode == "mock":
        return _parse_mock(query)

    try:
        driver = get_selenium_driver(site="wildberries")
        url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select("div.product-card")
        products = []

        for card in cards[:10]:
            name_tag = card.select_one("span.goods-name")
            price_tag = card.select_one("ins.price__lower-price")

            if not name_tag or not price_tag:
                continue

            name = name_tag.text.strip()
            price = int(price_tag.text.replace("₽", "").replace(" ", ""))
            link = "https://www.wildberries.ru" + card.find("a")["href"]

            products.append(Product(name=name, price=price, url=link))

        driver.quit()
        return products or _parse_mock(query)
    except Exception:
        return _parse_mock(query)


def _parse_mock(query: str) -> list[Product]:
    mock_path = Path("src/parser/mock/wildberries_mock.json")
    if not mock_path.exists():
        return []

    with open(mock_path, encoding="utf-8") as f:
        data = json.load(f)

    query = query.lower()
    return [
        Product(name=item["name"], price=item["price"], url=item["url"])
        for item in data
        if query in item["name"].lower()
    ]


