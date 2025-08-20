from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional, Iterable

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException,
)

from utils.selenium_driver import get_selenium_driver
from utils.helpers import human_sleep, load_site_cookies

GA_BASE = "https://goldapple.ru"
GA_PERFUMERY_SLUGS = ("/parfjumerija", "/parfyumeriya")

TAB_OPISANIE = "Описание"
TAB_PRIMENENIE = "Применение"
TAB_BREND = "Бренд"
TAB_DOP = "Дополнительная информация"

WAIT_SHORT = 8
WAIT_MED = 16
WAIT_LONG = 28

DESC_LIMIT = 200
INSTR_LIMIT = 200


@dataclass
class GAProduct:
    url: str = ""
    name: str = ""
    price: str = ""
    rating: str = ""
    description: str = ""
    instructions: str = ""
    country: str = ""


# ----------------- helpers -----------------


def _sleep(slow: bool, a: float = 0.3, b: float = 0.7) -> None:
    human_sleep(slow, a, b)


def _clean_text(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _shorten_text(s: str, limit: Optional[int]) -> str:
    if not s or not limit:
        return s or ""
    s = _clean_text(s)
    if len(s) <= limit:
        return s
    # по границе предложения, затем по слову
    m = re.search(rf"^(.{{0,{limit}}}[.!?])\s", s)
    if m and len(m.group(1)) >= int(limit * 0.6):
        return m.group(1).strip() + "…"
    cut = s[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip() + "…"


def _digits(text: str) -> str:
    return "".join(ch for ch in (text or "") if ch.isdigit())


def _on_not_found(driver) -> bool:
    try:
        body = (driver.page_source or "").lower()
        return "страница не найдена" in body
    except Exception:
        return False


def _dismiss_banners(driver) -> None:
    # cookies: «ХОРОШО»
    try:
        for xp in [
            "//button[normalize-space()='ХОРОШО']",
            "//button[contains(.,'ХОРОШО')]",
        ]:
            els = driver.find_elements(By.XPATH, xp)
            if els:
                els[0].click()
                break
    except Exception:
        pass
    # подтверждение города: «ДА, ВЕРНО»
    try:
        els = driver.find_elements(By.XPATH, "//button[normalize-space()='ДА, ВЕРНО']")
        if els:
            els[0].click()
    except Exception:
        pass


def _wait(driver, css: str, timeout: int = WAIT_MED):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )


# ----------------- category & links -----------------


def _open_perfumery_category(driver, slow: bool = False) -> bool:
    """Открывает рабочую категорию парфюмерии. Возвращает успех."""
    for slug in GA_PERFUMERY_SLUGS:
        driver.get(GA_BASE + slug)
        _sleep(slow, 0.6, 1.2)
        _dismiss_banners(driver)
        if _on_not_found(driver):
            continue
        # на странице должны появиться карточки-article
        try:
            _wait(driver, "article", timeout=WAIT_LONG)
            return True
        except TimeoutException:
            continue
    return False


def _is_good_product_url(url: str) -> bool:
    if not url:
        return False
    if url.startswith("/"):
        url = GA_BASE + url
    if not url.startswith(GA_BASE):
        return False
    return re.search(r"/\d{6,}-[a-z0-9\-]+$", url) is not None


def _grab_from_dom(driver) -> List[str]:
    hrefs: List[str] = []
    seen: set[str] = set()
    selectors = [
        "article a[href]",  # карточки в гриде
    ]
    for sel in selectors:
        try:
            anchors = driver.find_elements(By.CSS_SELECTOR, sel)
        except Exception:
            anchors = []
        for a in anchors:
            try:
                href = a.get_attribute("href") or ""
            except StaleElementReferenceException:
                continue
            if not href or href in seen:
                continue
            if href.startswith("/"):
                href = GA_BASE + href
            if _is_good_product_url(href):
                seen.add(href)
                hrefs.append(href)
    return hrefs


def _collect_links_infinite(driver, limit: int, slow: bool = False) -> List[str]:
    hrefs: List[str] = []
    seen: set[str] = set()
    idle = 0
    while True:
        new = _grab_from_dom(driver)
        added = 0
        for h in new:
            if h not in seen:
                seen.add(h)
                hrefs.append(h)
                added += 1
                if limit and len(hrefs) >= limit:
                    return hrefs
        idle = idle + 1 if added == 0 else 0
        if idle >= 8:
            return hrefs
        try:
            driver.execute_script("window.scrollBy(0, 1400);")
        except Exception:
            pass
        _sleep(slow, 0.15, 0.35)


# ----------------- PDP helpers -----------------


def _jsonld_product(page_source: str) -> dict:
    try:
        blocks = re.findall(
            r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
            page_source,
            flags=re.I | re.S,
        )
        for b in blocks:
            try:
                data = json.loads(b)
            except Exception:
                continue
            if isinstance(data, dict) and data.get("@type") in (
                "Product",
                "ProductGroup",
            ):
                return data
            if isinstance(data, list):
                for d in data:
                    if isinstance(d, dict) and d.get("@type") in (
                        "Product",
                        "ProductGroup",
                    ):
                        return d
    except Exception:
        pass
    return {}


def _find_name(driver) -> str:
    # строго внутри product-article
    try:
        el = driver.find_element(By.CSS_SELECTOR, "article h1")
        txt = _clean_text(el.text)
        if txt and "заказ" not in txt.lower():
            return txt
    except Exception:
        pass
    # itemprop=name в артикле
    try:
        el = driver.find_element(By.CSS_SELECTOR, "article [itemprop='name']")
        txt = _clean_text(el.text or el.get_attribute("content") or "")
        if txt:
            return txt
    except Exception:
        pass
    # JSON-LD
    j = _jsonld_product(driver.page_source)
    nm = j.get("name") if j else ""
    if nm:
        return _clean_text(nm)
    # og:title — самый запасной
    try:
        meta = driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']")
        content = meta.get_attribute("content") or ""
        return _clean_text(content)
    except Exception:
        return ""


def _price_from_dom(driver) -> str:
    # meta itemprop=price
    try:
        meta = driver.find_element(By.CSS_SELECTOR, "meta[itemprop='price']")
        val = meta.get_attribute("content") or ""
        if val:
            return _digits(val)
    except Exception:
        pass
    # видимая цена с ₽
    try:
        el = driver.find_element(By.XPATH, "//*[contains(., '₽') or contains(., 'Р')]")
        txt = _digits(el.text)
        return txt
    except Exception:
        return ""


def _rating_from_dom(driver) -> str:
    # JSON-LD
    try:
        j = _jsonld_product(driver.page_source)
        agg = j.get("aggregateRating") if j else None
        if isinstance(agg, dict):
            v = agg.get("ratingValue")
            if v:
                return str(v).replace(",", ".")
    except Exception:
        pass
    # визуальный бейдж «4.6»
    m = re.search(r">\s*([0-5]\.\d)\s*<", driver.page_source)
    return m.group(1) if m else ""


def _click_tab(driver, label: str) -> bool:
    want = label.strip()
    xps = [
        f"//button[.//div[contains(@class,'ga-tabs-tab__text') and normalize-space(text())='{want}']]",
        f"//button[normalize-space(.//div)='{want}']",
        f"//button[normalize-space(text())='{want}']",
    ]
    for xp in xps:
        try:
            els = driver.find_elements(By.XPATH, xp)
            if not els:
                continue
            btn = els[0]
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", btn
                )
            except Exception:
                pass
            WebDriverWait(driver, WAIT_SHORT).until(EC.element_to_be_clickable(btn))
            btn.click()
            _sleep(True, 0.12, 0.22)
            return True
        except Exception:
            continue
    return False


def _active_panel_text(driver) -> str:
    """
    Текст активной панели табов. У GA основной контейнер бывает .vSCKP ИЛИ .VSCKP.
    Берём кейс-инсенситивом + пару запасных селекторов.
    """
    xps = [
        # case-insensitive match for class contains 'vsckp'
        "//article//*[contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'vsckp')]",
        "//article//div[@itemprop='description']",
        # иногда кладут текст прямо в content-контейнер
        "//article//*[@data-test-id='content']//div[string-length(normalize-space(.))>0]",
    ]
    texts: list[str] = []
    for xp in xps:
        try:
            els = driver.find_elements(By.XPATH, xp)
            for e in els:
                t = (e.text or "").strip()
                if t:
                    texts.append(t)
            if texts:
                break
        except Exception:
            continue
    return _clean_text("\n".join(texts))


COUNTRIES = [
    "Россия",
    "РФ",
    "Беларусь",
    "Казахстан",
    "Франция",
    "Италия",
    "Испания",
    "Германия",
    "Швейцария",
    "США",
    "Великобритания",
    "ОАЭ",
    "Турция",
    "Польша",
    "Нидерланды",
    "Швеция",
    "Дания",
    "Ирландия",
    "Корея",
    "Южная Корея",
    "Япония",
    "Китай",
]


def _brand_country_short(driver) -> str:
    """
    На вкладке «Бренд» рядом с названием часто лежит одна короткая плашка-страна
    (див с классом типа pLsfM). Берём её, не завязываясь на точное имя класса.
    """
    try:
        xp = (
            "//article//*["
            "contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'plsf') "
            "or contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'country') "
            "or contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'flag')"
            "]"
        )
        els = driver.find_elements(By.XPATH, xp)
    except Exception:
        els = []
    for e in els:
        t = _clean_text(e.text)
        if t and len(t) <= 30:
            for c in COUNTRIES:
                if re.search(rf"\b{re.escape(c)}\b", t, flags=re.I):
                    return c
    # запасной: любые краткие строки внутри content-блока вкладки «Бренд»
    try:
        els2 = driver.find_elements(
            By.XPATH,
            "//article//*[@data-test-id='content']//div[string-length(normalize-space(.))<=30]",
        )
    except Exception:
        els2 = []
    for e in els2:
        t = _clean_text(e.text)
        for c in COUNTRIES:
            if re.search(rf"\b{re.escape(c)}\b", t, flags=re.I):
                return c
    return ""


def _country_from_panel(text: str) -> str:
    t = _clean_text(text)
    if not t:
        return ""
    m = re.search(r"страна происхождения\s*[:\-–—]?\s*([^\n\r]+)", t, flags=re.I)
    if m:
        return _clean_text(m.group(1))
    for c in COUNTRIES:
        if re.search(rf"\b{re.escape(c)}\b", t, flags=re.I):
            return c
    return ""


def _is_perfume_pdp(driver) -> bool:
    """Фильтр: PDP должен быть из раздела парфюмерии (проверяем «хлебные крошки»/ссылки)."""
    html = driver.page_source or ""
    return ("/parfjumerija" in html) or ("/parfyumeriya" in html)


# ----------------- parse product -----------------


def _read_tabs(driver, slow: bool) -> tuple[str, str, str]:
    description, instructions, country = "", "", ""

    _click_tab(driver, TAB_OPISANIE)
    _sleep(slow, 0.1, 0.25)
    description = _active_panel_text(driver)

    if _click_tab(driver, TAB_PRIMENENIE):
        _sleep(slow, 0.1, 0.25)
        instructions = _active_panel_text(driver)

    brand_text = ""
    if _click_tab(driver, TAB_BREND):
        _sleep(slow, 0.1, 0.25)
        brand_text = _active_panel_text(driver)
        # короткая страна «плашкой»
        short = _brand_country_short(driver)
        if short:
            country = short

    if not country and _click_tab(driver, TAB_DOP):
        _sleep(slow, 0.1, 0.25)
        country = _country_from_panel(_active_panel_text(driver))

    if not country and brand_text:
        country = _country_from_panel(brand_text)

    description = _shorten_text(description, DESC_LIMIT)
    instructions = _shorten_text(instructions, INSTR_LIMIT)
    return description, instructions, _clean_text(country)


def parse_product(driver, url: str, slow: bool = False) -> Optional[GAProduct]:
    try:
        driver.get(url)
        _sleep(slow, 0.6, 1.0)
        _dismiss_banners(driver)

        if _on_not_found(driver):
            return None

        # защита: на всякий выключаем «левые» товары
        if not _is_perfume_pdp(driver):
            return None

        name = _find_name(driver)
        price = _price_from_dom(driver)
        rating = _rating_from_dom(driver)
        description, instructions, country = _read_tabs(driver, slow)

        return GAProduct(
            url=url,
            name=name,
            price=price,
            rating=rating,
            description=description,
            instructions=instructions,
            country=country,
        )
    except WebDriverException:
        return None


# ----------------- public entry -----------------


def search_goldapple(
    mode: str = "real",
    *,
    limit: int = 100,
    slow: bool = False,
    use_profile: bool = False,
    profile_dir: str | None = None,
) -> List[GAProduct]:
    if mode == "mock":
        return []

    driver = get_selenium_driver(
        site="goldapple",
        headless=False,
        use_profile=use_profile,
        profile_dir=profile_dir,
    )
    items: List[GAProduct] = []
    try:
        load_site_cookies(driver, "goldapple", GA_BASE)
        _sleep(slow)

        if not _open_perfumery_category(driver, slow=slow):
            return items

        try:
            _wait(driver, "article", timeout=WAIT_LONG)
        except TimeoutException:
            return items

        links = _collect_links_infinite(driver, limit=limit or 100, slow=slow)
        # dedupe
        seen, uniq = set(), []
        for h in links:
            if h not in seen:
                seen.add(h)
                uniq.append(h)

        for href in uniq:
            p = parse_product(driver, href, slow=slow)
            if p:
                items.append(p)
            _sleep(slow, 0.12, 0.25)

        return items
    finally:
        try:
            driver.quit()
        except Exception:
            pass


