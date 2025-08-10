from pathlib import Path
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.selenium_driver import get_selenium_driver
from utils.selenium_helpers import load_site_cookies, human_sleep
from .base import Product
from .mock_parser import parse_mock_html


CITILINK_HOME = "https://www.citilink.ru/"


def _wait_citilink_cards(driver, timeout: int = 35):
    """Ждём контейнер и возвращаем список карточек (несколько вариантов селекторов)."""
    wait = WebDriverWait(driver, timeout)
    # контейнер списка
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.ProductCardVerticalList__root, div[data-meta-name='ProductVerticalList']")
        )
    )

    # варианты карточек
    for by, sel in [
        (By.CSS_SELECTOR, "article[data-meta-name='ProductVerticalSnippet']"),
        (By.CSS_SELECTOR, "div.ProductCardVertical"),
        (By.CSS_SELECTOR, "div.product_data__gtm-js"),  # старые вёрстки
    ]:
        cards = driver.find_elements(by, sel)
        if cards:
            return cards
    return []


def search_citilink(
    query: str,
    mode: str = "real",
    *,
    slow: bool = False,
    use_profile: bool = False,
    profile_dir: Optional[str] = None,
) -> List[Product]:
    """Парсер Citilink. В real идём через главную -> поле поиска (устойчивее), затем собираем карточки."""
    if mode == "mock":
        return parse_mock_html("citilink", query)

    driver = None
    try:
        driver = get_selenium_driver(site="citilink", use_profile=use_profile, profile_dir=profile_dir)
        load_site_cookies(driver, "citilink", CITILINK_HOME)
        human_sleep(slow)

        # через главную (прямые deep‑link часто упираются в антибот/редиректы)
        driver.get(CITILINK_HOME)
        human_sleep(slow, 0.6, 1.4)

        # поле поиска — несколько вариантов
        wait = WebDriverWait(driver, 25)
        search = None
        for sel in [
            "input[placeholder*='Найти']",
            "input[placeholder*='Поиск']",
            "input[type='search']",
            "input[name='text']",
        ]:
            try:
                search = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue

        if not search:
            Path("tests/citilink_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("citilink", query, "нет поля поиска")

        search.clear()
        search.send_keys(query)
        search.send_keys(Keys.ENTER)
        human_sleep(slow, 0.9, 1.8)

        # ждём карточки
        cards = _wait_citilink_cards(driver, timeout=35)
        if not cards:
            Path("tests/citilink_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("citilink", query, "нет карточек")

        # мягкая прокрутка, чтобы подгрузились цены
        for _ in range(2):
            try:
                driver.execute_script("window.scrollBy(0, 1200);")
            except Exception:
                pass
            human_sleep(slow, 0.3, 0.9)

        products: List[Product] = []

        for el in cards[:40]:
            try:
                # название
                name = ""
                for sel in [
                    "a[data-meta-name='Snippet__title']",
                    "a.ProductCardVertical__name",
                    "a.ProductCardVertical__name span",
                ]:
                    try:
                        t = el.find_element(By.CSS_SELECTOR, sel).text.strip()
                        if t:
                            name = t
                            break
                    except Exception:
                        pass

                # url
                url = ""
                for sel in [
                    "a[data-meta-name='Snippet__title']",
                    "a.ProductCardVertical__name",
                ]:
                    try:
                        href = el.find_element(By.CSS_SELECTOR, sel).get_attribute("href")
                        if href:
                            url = href
                            break
                    except Exception:
                        pass

                # цена
                price = "Нет цены"
                for sel in [
                    "span.ProductCardVerticalPrice__price-current_current-price",
                    "span[data-meta-price]",
                    "span.ProductCardVertical__price-current",
                ]:
                    try:
                        text = el.find_element(By.CSS_SELECTOR, sel).text
                        digits = "".join(ch for ch in text if ch.isdigit())
                        if digits:
                            price = int(digits)
                            break
                    except Exception:
                        pass

                if url:
                    products.append(Product(name=name or "Товар Citilink", price=price, url=url))
            except Exception:
                continue

        if not products:
            Path("tests/citilink_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("citilink", query, "пусто/селекторы")

        # топ‑10 уникальных
        uniq, seen = [], set()
        for p in products:
            key = (p.name, p.url)
            if key not in seen:
                uniq.append(p)
                seen.add(key)
            if len(uniq) == 10:
                break
        return uniq

    except Exception as e:
        return _fb("citilink", query, f"исключение: {e}")
    finally:
        if driver:
            driver.quit()


def _fb(site: str, query: str, reason: str):
    print(f"🔁 {site.upper()}: фолбэк на mock ({reason})")
    return parse_mock_html(site, query)

