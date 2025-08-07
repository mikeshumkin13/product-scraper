import time
from typing import List

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.selenium_driver import create_driver
from .base import Product



def search_dns(query: str, mode: str = "real") -> List[Product]:
    if mode != "real":
        raise ValueError("Только режим 'real' поддерживается для DNS")

    print("🌐 Открываем DNS...")
    url = f"https://www.dns-shop.ru/search/?q={query}"
    driver = create_driver()

    try:
        driver.get(url)
        time.sleep(5)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "catalog-product"))
        )

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        product_cards = soup.select("div.catalog-product")
        products = []

        for card in product_cards[:10]:
            try:
                name_tag = card.select_one("a.catalog-product__name")
                price_tag = card.select_one("div.catalog-product__price-current")
                link_tag = name_tag

                name = name_tag.get_text(strip=True) if name_tag else "Без названия"
                price = price_tag.get_text(strip=True).replace("\u2009", "") if price_tag else "Нет цены"
                url = "https://www.dns-shop.ru" + link_tag["href"] if link_tag and link_tag.has_attr("href") else ""

                products.append(Product(name=name, price=price, link=url, source="DNS"))
            except Exception:
                continue

        print(f"📦 DNS: найдено {len(products)}")
        return products

    except Exception as e:
        print("❌ DNS: ошибка —", e)
        return []

    finally:
        driver.quit()


