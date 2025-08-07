import time
from typing import List

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.selenium_driver import create_driver
from .base import Product



def search_citilink(query: str, mode: str = "real") -> List[Product]:
    if mode != "real":
        raise ValueError("Только режим 'real' поддерживается для Citilink")

    print("🌐 Открываем Citilink...")
    url = f"https://www.citilink.ru/search/?text={query}"
    driver = create_driver()

    try:
        driver.get(url)
        time.sleep(5)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ProductCardHorizontal__header-block"))
        )

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        product_cards = soup.select("div.ProductCardHorizontal")
        products = []

        for card in product_cards[:10]:
            try:
                name_tag = card.select_one(".ProductCardHorizontal__title")
                price_tag = card.select_one(".ProductCardHorizontal__price_current-price")
                link_tag = card.select_one("a.ProductCardHorizontal__title")

                name = name_tag.get_text(strip=True) if name_tag else "Без названия"
                price = price_tag.get_text(strip=True).replace("\u2009", "") if price_tag else "Нет цены"
                url = "https://www.citilink.ru" + link_tag["href"] if link_tag and link_tag.has_attr("href") else ""

                products.append(Product(name=name, price=price, link=url, source="Citilink"))
            except Exception:
                continue

        print(f"📦 Citilink: найдено {len(products)}")
        return products

    except Exception as e:
        print("❌ Citilink: ошибка —", e)
        return []

    finally:
        driver.quit()


