import time
from selenium.webdriver.common.by import By
from utils.selenium_driver import get_selenium_driver
from .base import Product
from parser.mock_parser import parse_mock_html


def search_dns(query: str, mode: str = "real") -> list[Product]:
    """
    Парсит сайт DNS Shop через Selenium или через mock-данные.

    Args:
        query (str): Поисковый запрос.
        mode (str): 'real' или 'mock'.

    Returns:
        list[Product]: Список найденных товаров.
    """
    if mode == "mock":
        return parse_mock_html("dns", query)

    try:
        driver = get_selenium_driver(site="dns", use_cookies=True)
        url = f"https://www.dns-shop.ru/search/?q={query}"
        driver.get(url)
        time.sleep(5)

        cards = driver.find_elements(By.CSS_SELECTOR, "div.catalog-product")
        products = []

        for card in cards[:10]:
            try:
                name = card.find_element(By.CSS_SELECTOR, "a.catalog-product__name").text
                price_str = card.find_element(By.CSS_SELECTOR, "span.product-buy__price").text
                price = int(price_str.replace("₽", "").replace(" ", ""))
                url = card.find_element(By.CSS_SELECTOR, "a.catalog-product__name").get_attribute("href")
                products.append(Product(name=name, price=price, url=url))
            except Exception:
                continue

        driver.quit()
        return products or parse_mock_html("dns", query)
    except Exception as e:
        if 'driver' in locals():
            driver.save_screenshot("dns_debug.png")
            with open("dns_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()
        return parse_mock_html("dns", query)


