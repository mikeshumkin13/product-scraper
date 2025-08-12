from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Set, Tuple
import json
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from curl_cffi import requests

from utils.selenium_driver import get_selenium_driver
from utils.selenium_helpers import load_site_cookies, human_sleep
from .base import Product
from .mock_parser import parse_mock_html


BASE = "https://www.ozon.ru/"
COMPOSER_API = "https://www.ozon.ru/api/composer-api.bx/page/json/v2?url="


def search_ozon(
    query: str,
    mode: str = "real",
    *,
    slow: bool = False,
    use_profile: bool = False,
    profile_dir: Optional[str] = None,
) -> List[Product]:
    """
    Ищем товары на Ozon:
    1) Открываем страницу поиска, подскролливаем, собираем ссылки на карточки
    2) Для каждой карточки вытягиваем SEO-блок из composer-api и достаем имя/цену
    """
    if mode == "mock":
        return parse_mock_html("ozon", query)

    search_url = f"{BASE}search/?text={query}&from_global=true"

    driver = None
    try:
        driver = get_selenium_driver(site="ozon", use_profile=use_profile, profile_dir=profile_dir)
        load_site_cookies(driver, "ozon", BASE)
        human_sleep(slow)

        driver.get(search_url)
        human_sleep(slow)

        # ждём контейнер с результатами
        wait = WebDriverWait(driver, 25)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widget='searchResultsV2']"))
        )

        # немного прокрутим, чтобы подгрузились карточки
        _smart_scroll(driver, steps=20 if slow else 8)

        # сохраним html для отладки
        Path("tests/ozon_real.html").write_text(driver.page_source, encoding="utf-8")

        # собираем product-ссылки
        links = _collect_product_links(driver)
        if not links:
            return _fb("ozon", query, "пусто/не нашли карточек")

        # переносим куки из Selenium → curl_cffi.Session (лучше проходит антибот)
        session = _make_curl_session_with_cookies(driver)

        # тянем детали карточек через composer-api
        products: List[Product] = []
        seen: Set[Tuple[str, str]] = set()

        for href in links[:40]:
            try:
                data = _fetch_product_via_api(session, href)
                if not data:
                    continue
                name, price_int, url = data
                key = (name, url)
                if key in seen:
                    continue
                products.append(Product(name=name, price=price_int, url=url))
                seen.add(key)
                if len(products) == 10:
                    break
                if slow:
                    time.sleep(0.15)
            except Exception:
                continue

        return products if products else _fb("ozon", query, "пусто/после api")
    except Exception as e:
        return _fb("ozon", query, f"исключение: {e}")
    finally:
        if driver:
            driver.quit()


# ---------- helpers ----------

def _smart_scroll(driver, *, steps: int = 10, dy: int = 700):
    for _ in range(max(1, steps)):
        driver.execute_script(f"window.scrollBy(0, {dy});")
        time.sleep(0.05)


def _collect_product_links(driver) -> List[str]:
    container = driver.find_element(By.CSS_SELECTOR, "div[data-widget='searchResultsV2']")
    anchors = container.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
    hrefs: List[str] = []
    for a in anchors:
        href = a.get_attribute("href") or ""
        if not href:
            continue
        # Нормализуем: composer ждёт url с ведущим '/'
        # Пример: '/product/chaynik-....-1234567890'
        if "://www.ozon.ru" in href:
            idx = href.find("/product/")
            if idx != -1:
                href = href[idx:]
        if href.startswith("/product/") and href not in hrefs:
            hrefs.append(href)
    return hrefs


def _make_curl_session_with_cookies(driver) -> requests.Session:
    s = requests.Session()
    # небольшой прогрев (получить server-side куки)
    s.get(BASE, timeout=20)

    # переносим куки из selenium
    for c in driver.get_cookies():
        try:
            s.cookies.set(
                c.get("name"),
                c.get("value"),
                domain=c.get("domain") or ".ozon.ru",
                path=c.get("path") or "/",
                secure=bool(c.get("secure")),
                expires=c.get("expiry"),
                rest={"HttpOnly": c.get("httpOnly")},
            )
        except Exception:
            continue
    return s


def _fetch_product_via_api(session: requests.Session, product_href: str) -> Optional[Tuple[str, int, str]]:
    """
    Возвращает (name, price_int, full_url) или None
    """
    api_url = f"{COMPOSER_API}{product_href}"
    r = session.get(api_url, timeout=30)
    if r.status_code != 200:
        return None

    data = r.json()

    # В некоторых случаях приходит adult modal — пропускаем
    if data.get("layout") and data["layout"][0].get("component") == "userAdultModal":
        return None

    seo = data.get("seo") or {}
    scripts = seo.get("script") or []
    if not scripts:
        return None

    try:
        inner = scripts[0]["innerHTML"]
        inner_json = json.loads(inner)
        name = seo.get("title") or inner_json.get("name") or inner_json.get("headline") or ""
        # цена — число (без пробелов), валюта не нужна для Product
        price_str = str(inner_json.get("offers", {}).get("price", "")).replace("\u00a0", "").replace(" ", "")
        price_int = int("".join(ch for ch in price_str if ch.isdigit())) if price_str else 0
        full_url = BASE.rstrip("/") + product_href
        if not name:
            return None
        return name, price_int, full_url
    except Exception:
        return None


def _fb(site: str, query: str, reason: str) -> List[Product]:
    print(f"🔁 {site.upper()}: фолбэк на mock ({reason})")
    return parse_mock_html(site, query)

