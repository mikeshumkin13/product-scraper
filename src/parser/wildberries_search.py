import os
import time
from typing import List

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from parser.base import Product
from utils.selenium_driver import create_driver


def search_wildberries(query: str, mode: str = "real") -> List[Product]:
    """
    Поиск товаров на сайте Wildberries в режиме 'real' с использованием Selenium.
    Сохраняет HTML страницы в wb_debug.html для отладки.
    Возвращает список объектов Product.
    """
    if mode != "real":
        raise ValueError("Поддерживается только режим 'real' для Wildberries")

    print("🌐 Открываем Wildberries...")
    url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
    driver = create_driver()

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        # Ждём появления хотя бы одной карточки товара
        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "article.product-card")
                )
            )
        except Exception as e:
            print("⚠️ Не удалось дождаться карточек товаров:", e)

        # Скроллим вниз, чтобы догрузить больше товаров
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(2)

        html = driver.page_source
        with open("wb_debug.html", "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, "html.parser")
        product_cards = soup.select("article.product-card")

        products: List[Product] = []

        for card in product_cards[:10]:  # до 10 товаров
            name_tag = card.select_one("a.product-card__main")
            name = name_tag.get("aria-label") or name_tag.get_text(strip=True) if name_tag else "Без названия"

            price_tag = card.select_one("span.price__lower-price")
            price = price_tag.get_text(strip=True).replace("\u2009", "") if price_tag else "Нет цены"

            href = name_tag["href"] if name_tag and name_tag.has_attr("href") else ""
            full_url = "https://www.wildberries.ru" + href if href else url

            products.append(Product(name=name, price=price, url=full_url))

        print(f"📦 Wildberries: найдено {len(products)}")
        return products

    except Exception as e:
        print("❌ Wildberries: ошибка —", e)
        return []

    finally:
        driver.quit()


