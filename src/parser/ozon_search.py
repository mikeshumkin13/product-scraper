from __future__ import annotations

import time
import json
from typing import List, Dict, Iterable

from bs4 import BeautifulSoup
from curl_cffi import requests
from selenium.webdriver.common.by import By

from utils.selenium_driver import get_selenium_driver

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
    s = requests.Session()
    s.get(BASE, timeout=20)
    for c in driver.get_cookies():
        try:
            s.cookies.set(
                c["name"],
                c.get("value", ""),
                domain=c.get("domain", ".ozon.ru"),
                path=c.get("path", "/"),
            )
        except Exception:
            pass
    return s


def _collect_product_hrefs(driver, slow: bool) -> List[str]:
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
        if href.startswith("/product/"):
            href = BASE + href
        if "/product/" in href and href not in seen:
            seen.add(href)
            hrefs.append(href)
    return hrefs


def _fetch_product_info(session: requests.Session, product_url: str) -> Dict:
    path = product_url.replace(BASE, "")
    if not path.startswith("/"):
        path = "/" + path

    r = session.get(COMPOSER + path, timeout=25)
    r.raise_for_status()
    data = json.loads(r.content.decode("utf-8", "ignore"))

    seo = data.get("seo", {})
    scripts = seo.get("script", [])
    if not scripts:
        title = seo.get("title") or ""
        return {"name": title, "price": None, "currency": None, "url": product_url, "image": None}

    ld = scripts[0].get("innerHTML", "")
    ld_json = json.loads(ld)

    name = ld_json.get("name") or ld_json.get("description") or seo.get("title") or ""
    offers = ld_json.get("offers") or {}
    price = offers.get("price")
    currency = offers.get("priceCurrency")
    image = ld_json.get("image")

    return {"name": name, "price": price, "currency": currency, "url": product_url, "image": image}


def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def search_ozon(
    query: str,
    mode: str = "real",
    slow: bool = False,
    *,
    use_profile: bool = False,
    profile_dir: str | None = None,
) -> List[Dict]:
    """
    Возвращает список dict: {name, price, currency, url, image}.
    Совместимо с main.py, поддерживает use_profile/profile_dir.
    """
    if mode == "mock":
        from pathlib import Path
        html = Path("src/parser/mock/ozon_mock.html").read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        hrefs = [BASE + a["href"] for a in soup.select("a[href^='/product/']")]
        hrefs = _dedupe_keep_order(hrefs)[:10]
        return [{"name": "MOCK item", "price": None, "currency": None, "url": h, "image": None} for h in hrefs]

    driver = get_selenium_driver(
        site="ozon",
        headless=False,
        use_profile=use_profile,
        profile_dir=profile_dir,
    )
    try:
        search_url = f"{BASE}/search/?text={query}&from_global=true"
        driver.get(search_url)
        if slow:
            _human_sleep(1.0)

        # мягко кликаем согласие на cookies, если всплыло
        try:
            consent = driver.find_elements(By.XPATH, "//button[contains(., 'Согласен') or contains(., 'Я согласен')]")
            if consent:
                consent[0].click()
                if slow:
                    _human_sleep(0.5)
        except Exception:
            pass

        hrefs = _collect_product_hrefs(driver, slow=slow)
        if len(hrefs) < 10:
            _scroll(driver, steps=30, slow=slow)
            hrefs = _collect_product_hrefs(driver, slow=slow)

        hrefs = _dedupe_keep_order(hrefs)[:10]
        if not hrefs:
            return []

        session = _copy_cookies_to_session(driver)

        out: List[Dict] = []
        for h in hrefs:
            try:
                item = _fetch_product_info(session, h)
                if item.get("name"):
                    out.append(item)
            except Exception:
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


