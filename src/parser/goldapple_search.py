"""Парсер раздела «Парфюмерия» Gold Apple.

Собирает url, name, price, rating, description, instructions, country.
Селекторы и эвристики рассчитаны на актуальную вёрстку Gold Apple.
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

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
from parser.entities import GAProduct
from parser.constants import (
    GA_BASE,
    GA_PERFUMERY_SLUGS,
    TAB_OPISANIE,
    TAB_PRIMENENIE,
    TAB_BREND,
    TAB_DOP,
    WAIT_SHORT,
    WAIT_MED,
    WAIT_LONG,
    DESC_LIMIT,
    INSTR_LIMIT,
    COUNTRIES,
)
from utils.text_utils import (
    clean_text as _clean_text,
    shorten_text as _shorten_text,
    digits as _digits,
)


# ----------------- helpers -----------------


def _sleep(slow: bool, a: float = 0.3, b: float = 0.7) -> None: # pragma: no cover
    human_sleep(slow, a, b)


def _on_not_found(driver) -> bool: # pragma: no cover
    try:
        body = (driver.page_source or "").lower()
        return "страница не найдена" in body
    except Exception:
        return False


def _dismiss_banners(driver) -> None: # pragma: no cover
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


def _wait(driver, css: str, timeout: int = WAIT_MED): # pragma: no cover
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )


# ----------------- category & links -----------------


def _open_perfumery_category(driver, slow: bool = False) -> bool: # pragma: no cover
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


def _is_good_product_url(url: str) -> bool: # pragma: no cover
    if not url:
        return False
    if url.startswith("/"):
        url = GA_BASE + url
    if not url.startswith(GA_BASE):
        return False
    return re.search(r"/\d{6,}-[a-z0-9\-]+$", url) is not None


def _grab_from_dom(driver) -> List[str]: # pragma: no cover
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


# --- стабильный сбор ссылок ---


def _collect_links_paged(
    driver, base_url: str, limit: int, slow: bool = False
) -> List[str]: # pragma: no cover
    """Обходит страницы каталога по ``?p=1,2,...`` и собирает ссылки.

    Args:
        driver: Selenium WebDriver.
        base_url: Базовый URL категории без параметров.
        limit: Максимум ссылок к сбору.
        slow: Включить человеко-паузы.

    Returns:
        Список уникальных ссылок на PDP (до ``limit`` штук).
    """
    hrefs: List[str] = []
    seen: set[str] = set()
    page = 1
    empty_pages = 0

    while len(hrefs) < limit and empty_pages < 2:  # две пустые подряд — конец каталога
        url = f"{base_url}?p={page}"
        driver.get(url)
        _sleep(slow, 0.6, 1.2)
        _dismiss_banners(driver)
        try:
            _wait(driver, "article", timeout=WAIT_MED)
        except TimeoutException:
            empty_pages += 1
            page += 1
            continue

        added_here = 0
        for h in _grab_from_dom(driver):
            if h not in seen:
                seen.add(h)
                hrefs.append(h)
                added_here += 1
                if len(hrefs) >= limit:
                    break

        empty_pages = 0 if added_here else empty_pages + 1
        page += 1

    return hrefs[:limit]


def _collect_links_infinite(driver, limit: int, slow: bool = False) -> List[str]: # pragma: no cover
    """Собирает ссылки из бесконечного скролла.

    Прокручивает страницу вниз и ждёт, пока реально вырастет число ``article``.
    Ограничивается ``limit`` и счётчиком стагнации.
    """
    hrefs: List[str] = []
    seen: set[str] = set()
    stagnation = 0
    cards_sel = "article"
    last_cards = 0

    while len(hrefs) < limit and stagnation < 6:
        # 1) собрать всё, что есть сейчас
        added = 0
        for h in _grab_from_dom(driver):
            if h not in seen:
                seen.add(h)
                hrefs.append(h)
                added += 1
                if len(hrefs) >= limit:
                    return hrefs

        # 2) проскроллить в самый низ
        try:
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight - 200);"
            )
        except Exception:
            pass

        # 3) подождать реальный прирост количества article
        grew = False
        for _ in range(30):  # ~3–6 сек с короткими паузами
            try:
                cur = len(driver.find_elements(By.CSS_SELECTOR, cards_sel))
            except Exception:
                cur = last_cards
            if cur > last_cards:
                last_cards = cur
                grew = True
                break
            _sleep(True, 0.10, 0.20)

        stagnation = 0 if (added or grew) else (stagnation + 1)

    return hrefs[:limit]


# ----------------- PDP helpers -----------------


def _jsonld_product(page_source: str) -> dict: # pragma: no cover
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


def _find_name(driver) -> str: # pragma: no cover
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


def _price_from_dom(driver) -> str: # pragma: no cover
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


def _rating_from_dom(driver) -> str: # pragma: no cover
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


def _click_tab(driver, label: str) -> bool: # pragma: no cover
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


def _active_panel_text(driver) -> str: # pragma: no cover
    """Возвращает текст активной панели табов на PDP.

    Ищет контейнеры вида ``.vSCKP/.VSCKP`` и альтернативные блоки внутри ``article``.
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


def _brand_country_short(driver) -> str: # pragma: no cover
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


def _country_from_panel(text: str) -> str: # pragma: no cover
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


def _read_tabs(driver, slow: bool) -> tuple[str, str, str]: # pragma: no cover
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


def parse_product(driver, url: str, slow: bool = False) -> Optional[GAProduct]: # pragma: no cover
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
) -> List[GAProduct]: # pragma: no cover
    """Точка входа: собирает товары из раздела «Парфюмерия».

    Args:
        mode: 'real' | 'mock'. В 'mock' возвратит пустой список.
        limit: Макс. количество товаров к сбору.
        slow: Человеко-паузы (медленнее, но стабильнее).
        use_profile: Поднять Chrome с указанным профилем.
        profile_dir: Папка профиля Chrome.

    Returns:
        Список ``GAProduct`` для выгрузки в CSV.
    """
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

        category_url = driver.current_url.split("?", 1)[0]  # чистый URL категории
        links = _collect_links_paged(
            driver, category_url, limit=limit or 100, slow=slow
        )
        if len(links) < (limit or 100) // 3:  # на случай, если пагинации нет/сломалась
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
