import time
from selenium.webdriver.common.by import By
from utils.selenium_driver import get_selenium_driver
from .base import Product
from parser.mock_parser import parse_mock_html


def search_ozon(query: str, mode: str = "real") -> list[Product]:
    """
    Парсит Ozon через Selenium или mock-данные.

    Args:
        query (str): Название товара.
        mode (str): Режим: 'real' или 'mock'.

    Returns:
        list[Product]: Найденные товары.
    """
    if mode == "mock":
        return parse_mock_html("ozon", query)

    try:
        driver = get_selenium_driver(site="ozon", use_cookies=True)
        url = f"https://www.ozon.ru/search/?text={query}"
        driver.get(url)
        time.sleep(5)

        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-widget='searchResultsV2'] article")
        products = []

        for card in cards[:10]:
            try:
                name = card.find_element(By.CSS_SELECTOR, "a span").text
                price_tag = card.find_element(By.CSS_SELECTOR, "span[style*='color:black']")
                price = int(price_tag.text.replace("₽", "").replace(" ", ""))
                url = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                products.append(Product(name=name, price=price, url=url))
            except Exception:
                continue

        driver.quit()
        return products or parse_mock_html("ozon", query)
    except Exception as e:
        if 'driver' in locals():
            driver.save_screenshot("ozon_debug.png")
            with open("ozon_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.quit()
        return parse_mock_html("ozon", query)
