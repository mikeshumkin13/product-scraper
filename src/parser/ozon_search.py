import time
from typing import List

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.selenium_driver import create_driver
from .base import Product



def search_ozon(query: str, mode: str = "real") -> List[Product]:
    if mode != "real":
        raise ValueError("Только режим 'real' поддерживается для Ozon")

    print("🌐 Открываем Ozon...")
    url = f"https://www.ozon.ru/search/?text={query}"
    driver = create_driver()

    try:
        driver.get(url)
        time.sleep(5)

        # Обход защиты: кнопка "Обновить"
        try:
            reload_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "reload-button"))
            )
            print("🔁 Обнаружена защита. Кликаем 'Обновить'...")
            reload_btn.click()
            time.sleep(5)
        except Exception:
            pass

        # Ждём появления результатов
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widget='searchResultsV2']"))
        )

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        product_cards = soup.select("div[data-widget='searchResultsV2'] article")
        products = []

        for card in product_cards[:10]:
            try:
                name_tag = card.select_one("span")
                price_tag = card.select_one("span[class*=price]")
                link_tag = card.select_one("a")

                name = name_tag.get_text(strip=True) if name_tag else "Без названия"
                price = price_tag.get_text(strip=True).replace("\u2009", "") if price_tag else "Нет цены"
                url = "https://www.ozon.ru" + link_tag["href"] if link_tag and link_tag.has_attr("href") else ""

                products.append(Product(name=name, price=price, link=url, source="Ozon"))
            except Exception:
                continue

        print(f"📦 Ozon: найдено {len(products)}")
        return products

    except Exception as e:
        print("❌ Ozon: ошибка —", e)
        return []

    finally:
        driver.quit()


