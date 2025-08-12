from __future__ import annotations

import time
import json
from typing import List, Dict, Iterable

from bs4 import BeautifulSoup
from curl_cffi import requests
from selenium.webdriver.common.by import By

from utils.selenium_driver import get_selenium_driver
from parser.base import Product  # чтобы типы не ругались, но возвращаем dict


BASE = "https://www.ozon.ru"
COMPOSER = f"{BASE}/api/composer-api.bx/page/json/v2?url="


def _human_sleep(s: float) -> None:
    time.sleep(s)


def _scroll(driver, steps: int = 20, dy: int = 600, slow: bool = False) -> None:
    for _ in range(steps):
        driver.execute_script(f"window.scrollBy(0, {dy});")
        if slow:
            _human_sleep(0.15)


def _copy_cookies_to_session(driver) -> requests.Session:
    """
    Переносим куки из Selenium в curl_cffi.Session, чтобы API отдало данные.
    """
    s = requests.Session()
    # простая и достаточная прогревка домена
    s.get(BASE, timeout=20)
    for c in driver.get_cookies():
        # минимально необходимое: name/value/domain/path
        try:
            s.cookies.set(c["name"], c.get("value", ""), domain=c.get("domain", ".ozon.ru"), path=c.get("path", "/"))
        except Exception:
            pass
    return s


def _collect_product_hrefs(driver, slow: bool) -> List[str]:
    """
    Берём все ссылки вида /product/… на странице поиска.
    """
    _scroll(driver, steps=24, slow=slow)
    anchors = driver.find_elements(By.CSS_SELECTOR, "a[href^='/product/']")
    hrefs: List[str] = []
    seen = set()
    for a in anchors:
        try:
            href = a.get_attribute("href") or ""
        except Exception:
            continue
        if not href:
            continue
        # нормализуем
        if href.startswith("/product/"):
            href = BASE + href
        if "/product/" in href and href not in seen:
            seen.add(href)
            hrefs.append(href)
    return hrefs


def _fetch_product_info(session: requests.Session, product_url: str) -> Dict:
    """
    Достаём карточку через composer API.
    Возвращаем dict: name, price, currency, url, image
    """
    # в API передаём только путь после домена
    path = product_url.replace(BASE, "")
    if not path.startswith("/"):
        path = "/" + path

    r = session.get(COMPOSER + path, timeout=25)
    r.raise_for_status()
    data = json.loads(r.content.decode("utf-8", "ignore"))

    # Вся rich‑инфа есть в seo.script[0].innerHTML (JSON‑LD)
    seo = data.get("seo", {})
    scripts = seo.get("script", [])
    if not scripts:
        # бывает, что adult modal или нет seo — мягко отвалимся
        title = seo.get("title") or ""
        return {
            "name": title,
            "price": None,
            "currency": None,
            "url": product_url,
            "image": None,
        }

    ld = scripts[0].get("innerHTML", "")
    ld_json = json.loads(ld)

    name = ld_json.get("name") or ld_json.get("description") or seo.get("title") or ""
    offers = ld_json.get("offers") or {}
    price = offers.get("price")
    currency = offers.get("priceCurrency")
    image = ld_json.get("image")

    return {
        "name": name,
        "price": price,
        "currency": currency,
        "url": product_url,
        "image": image,
    }


def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def search_ozon(query: str, mode: str = "real", slow: bool = False) -> List[Dict]:
    """
    Возвращает список dict: {name, price, currency, url, image}.
    MOCK: берём из parser/mock/ozon_mock.html (совместимость).
    REAL: открываем поиск, вытаскиваем ссылки и бьёмся в composer‑API.
    """
    if mode == "mock":
        # совместимость со старыми тестами: читаем локальный HTML и парсим <a href="/product/...">
        from pathlib import Path
        html = Path("src/parser/mock/ozon_mock.html").read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        hrefs = []
        for a in soup.select("a[href^='/product/']"):
            hrefs.append(BASE + a["href"])
        hrefs = _dedupe_keep_order(hrefs)[:40]
        # без сессии — просто оформим заглушки
        return [{"name": "MOCK item", "price": None, "currency": None, "url": h, "image": None} for h in hrefs]

    # REAL
    driver = get_selenium_driver(site="ozon", headless=False)
    try:
        search_url = f"{BASE}/search/?text={query}&from_global=true"
        driver.get(search_url)
        if slow:
            _human_sleep(1.0)

        # принять cookies, если вдруг всплыли — мягкий try
        try:
            # на всякий поставим клик по кнопке согласия, если есть
            consent = driver.find_elements(By.XPATH, "//button[contains(., 'Согласен') or contains(., 'Я согласен')]")
            if consent:
                consent[0].click()
                if slow:
                    _human_sleep(0.5)
        except Exception:
            pass

        hrefs = _collect_product_hrefs(driver, slow=slow)
        # подстрахуемся, что на первых экранах мало ссылок — докрутим ещё
        if len(hrefs) < 10:
            _scroll(driver, steps=30, slow=slow)
            hrefs = _collect_product_hrefs(driver, slow=slow)

        hrefs = _dedupe_keep_order(hrefs)[:40]  # хватит 40 карточек на запрос

        if not hrefs:
            return []

        session = _copy_cookies_to_session(driver)

        out: List[Dict] = []
        for h in hrefs:
            try:
                item = _fetch_product_info(session, h)
                # минимальная валидация
                if item.get("name"):
                    out.append(item)
            except Exception:
                # мягко игнорим проблемные карточки
                continue
            finally:
                if slow:
                    _human_sleep(0.15)

        return out
    finally:
        try:
            driver.quit()
        except Exception:
            pass

