from pathlib import Path
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.selenium_driver import get_selenium_driver
from utils.helpers import load_site_cookies, human_sleep
from .base import Product
from .mock_parser import parse_mock_html


DNS_HOME = "https://www.dns-shop.ru/"


def _dismiss_dns_modals(driver):
    # подтверждение региона / cookies — A/B
    candidates = [
        "button[aria-label*='Да']",
        "button[data-qa='region-confirm-button']",
        "button.ui-button_blue",
        "button.cookies__button",
        "button:has(span:contains('Принять'))",
    ]
    for sel in candidates:
        try:
            el = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            el.click()
            human_sleep(True, 0.2, 0.6)
        except Exception:
            pass


def _wait_dns_cards(driver, timeout=30):
    wait = WebDriverWait(driver, timeout)
    # ждём контейнер результатов
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.catalog-products, div.products-page")
        )
    )
    # несколько вариантов карточек
    for by, sel in [
        (By.CSS_SELECTOR, "div.catalog-product"),
        (By.CSS_SELECTOR, "div.product-card"),
        (By.CSS_SELECTOR, "a.catalog-product__name"),
    ]:
        els = driver.find_elements(by, sel)
        if els:
            return els
    return []


def search_dns(
    query: str,
    mode: str = "real",
    *,
    slow: bool = False,
    use_profile: bool = False,
    profile_dir: str | None = None,
) -> List[Product]:
    if mode == "mock":
        return parse_mock_html("dns", query)

    driver = None
    try:
        driver = get_selenium_driver(
            site="dns", use_profile=use_profile, profile_dir=profile_dir
        )
        load_site_cookies(driver, "dns", DNS_HOME)
        human_sleep(slow)

        # ИДЁМ ТОЛЬКО ЧЕРЕЗ ГЛАВНУЮ + поле поиска (прямая /search/?q=... часто 403)
        driver.get(DNS_HOME)
        human_sleep(slow, 0.6, 1.2)
        _dismiss_dns_modals(driver)

        # Поле поиска
        wait = WebDriverWait(driver, 25)
        search = None
        for sel in [
            "input[placeholder*='Поиск']",
            "input#search-input",
            "input[type='search']",
        ]:
            try:
                search = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue
        if not search:
            Path("tests/dns_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("dns", query, "нет поля поиска")

        search.clear()
        search.send_keys(query)
        search.send_keys(Keys.ENTER)
        human_sleep(slow, 1.0, 1.8)

        cards = _wait_dns_cards(driver, timeout=35)
        if not cards:
            Path("tests/dns_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("dns", query, "нет карточек")

        # лёгкая прокрутка чтобы прогрузились цены
        for _ in range(2):
            try:
                driver.execute_script("window.scrollBy(0, 1000);")
            except Exception:
                pass
            human_sleep(slow, 0.3, 0.8)

        products: List[Product] = []
        for card in cards[:30]:
            try:
                # название + ссылка
                url = name = ""
                try:
                    a = card.find_element(By.CSS_SELECTOR, "a.catalog-product__name")
                except Exception:
                    a = card if card.tag_name == "a" else None
                if a:
                    name = (a.text or a.get_attribute("title") or "").strip()
                    url = a.get_attribute("href") or ""

                # цена
                price_text = ""
                for sel in [
                    "div.product-buy__price",
                    "div.price__current",
                    "span.price",
                ]:
                    try:
                        price_text = card.find_element(By.CSS_SELECTOR, sel).text
                        if price_text:
                            break
                    except Exception:
                        pass
                digits = "".join(ch for ch in price_text if ch.isdigit())
                price = int(digits) if digits else "Нет цены"

                if url:
                    products.append(
                        Product(name=name or "Товар DNS", price=price, url=url)
                    )
            except Exception:
                continue

        if not products:
            Path("tests/dns_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("dns", query, "пусто/селекторы")

        # нормализуем топ‑10
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
        return _fb("dns", query, f"исключение: {e}")
    finally:
        if driver:
            driver.quit()


def _fb(site: str, query: str, reason: str):
    print(f"🔁 {site.upper()}: фолбэк на mock ({reason})")
    return parse_mock_html(site, query)
