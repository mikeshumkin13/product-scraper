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


OZON_HOME = "https://www.ozon.ru/"


def _ozon_accept_cookies(driver):
    selectors = [
        "[data-widget='cookie-notice'] button[type='button']",
        "div[data-widget*='cookie'] button",
        "button:has(span:contains('OK'))",
    ]
    for sel in selectors:
        try:
            el = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            el.click()
            human_sleep(True, 0.2, 0.6)
            return
        except Exception:
            pass


def _wait_ozon_cards(driver, timeout=30):
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-widget='searchResultsV2']")))
    # набор вариантов ссылок карточек
    variants = [
        (By.CSS_SELECTOR, "a.tile-hover-target"),
        (By.CSS_SELECTOR, "[data-widget='searchResultsV2'] a[href*='/product/']"),
    ]
    for by, sel in variants:
        els = driver.find_elements(by, sel)
        if els:
            return els
    # подскроллим и попробуем ещё раз
    try:
        driver.execute_script("window.scrollBy(0, 1200);")
    except Exception:
        pass
    human_sleep(True, 0.3, 0.9)
    return driver.find_elements(By.CSS_SELECTOR, "a.tile-hover-target")


def search_ozon(
    query: str,
    mode: str = "real",
    *,
    slow: bool = False,
    use_profile: bool = False,
    profile_dir: str | None = None,
) -> List[Product]:
    if mode == "mock":
        return parse_mock_html("ozon", query)

    driver = None
    try:
        driver = get_selenium_driver(site="ozon", use_profile=use_profile, profile_dir=profile_dir)
        load_site_cookies(driver, "ozon", OZON_HOME)
        human_sleep(slow)

        # идём через главную и поле поиска (надёжнее)
        driver.get(OZON_HOME)
        human_sleep(slow, 0.6, 1.4)

        _ozon_accept_cookies(driver)

        wait = WebDriverWait(driver, 25)
        search = None
        for sel in ["input[placeholder*='Искать']", "input[name='text']", "input[type='search']"]:
            try:
                search = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue
        if not search:
            Path("tests/ozon_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("ozon", query, "нет поля поиска")

        search.clear()
        search.send_keys(query)
        search.send_keys(Keys.ENTER)
        human_sleep(slow, 0.8, 1.6)

        cards = _wait_ozon_cards(driver, timeout=35)
        if not cards:
            Path("tests/ozon_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("ozon", query, "нет карточек")

        # мягкая прокрутка
        for _ in range(3):
            try:
                driver.execute_script("window.scrollBy(0, 900);")
            except Exception:
                pass
            human_sleep(slow, 0.2, 0.6)

        products: List[Product] = []
        for a in cards[:50]:
            try:
                href = a.get_attribute("href") or ""
                if not href:
                    continue
                name = (a.get_attribute("title") or a.get_attribute("aria-label") or a.text or "").strip()
                if not name:
                    name = "Товар Ozon"

                # цена — ближайший span с ₽ в пределах «плитки»
                price_text = ""
                try:
                    price_el = a.find_element(
                        By.XPATH,
                        ".//ancestor::div[contains(@class,'tile')][1]//span[contains(., '₽')]"
                    )
                    price_text = price_el.text
                except Exception:
                    pass
                digits = "".join(ch for ch in price_text if ch.isdigit())
                price = int(digits) if digits else "Нет цены"

                products.append(Product(name=name, url=href, price=price))
            except Exception:
                continue

        if not products:
            Path("tests/ozon_real.html").write_text(driver.page_source, encoding="utf-8")
            return _fb("ozon", query, "пусто/антибот")

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
        return _fb("ozon", query, f"исключение: {e}")
    finally:
        if driver:
            driver.quit()


def _fb(site: str, query: str, reason: str):
    print(f"🔁 {site.upper()}: фолбэк на mock ({reason})")
    return parse_mock_html(site, query)


