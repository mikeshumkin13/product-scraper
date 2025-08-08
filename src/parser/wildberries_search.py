import time
from selenium.webdriver.common.by import By
from utils.selenium_driver import get_selenium_driver
from .base import Product
from parser.mock_parser import parse_mock_json


def search_wildberries(query: str, mode: str = "real") -> list[Product]:
    """
    Парсит Wildberries через Selenium или mock.

    Args:
        query (str): Название товара.
        mode (str): 'real' или 'mock'.

    Returns:
        list[Product]: Найденные товары.
    """
    if mode == "mock":
        return parse_mock_json("wildberries", query)

    try:
        driver = get_selenium_driver(site="wildberries", use_cookies=True)
        url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
        driver.get(url)
        time.sleep(5)

        cards = driver.find_elements(By.CSS_SELECTOR, "div.product-card")
        products = []

        for card in cards[:10]:
            try:
                name = card.find_element(By.CSS_SELECTOR, "span.goods-name").text
                price_str = card.find_element(By.CSS_SELECTOR, "ins.lower-price").text
                price = int(price_str.replace("₽", "").replace(" ", ""))
                url = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                products.append(Product(name=name, price=price, url=url))
            except Exception:
                continue

        driver.quit()
        return products or parse_mock_json("wildberries", query)
    except Exception as e:
        if 'driver' in locals():
            driver.save_screenshot("wildberries_debug.png")
            with open("wildberries_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()
        return parse_mock_json("wildberries", query)


