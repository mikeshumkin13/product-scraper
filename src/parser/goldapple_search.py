# src/goldapple_search.py
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.selenium_driver import get_selenium_driver

BASE = "https://goldapple.ru"
SECTION = f"{BASE}/parfjumerija"


# ──────────────────────────────────────────────────────────────────────────────
# Модель
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class GAProduct:
    url: str
    name: str
    price: str
    rating: str
    description: str
    instructions: str
    country: str


# ──────────────────────────────────────────────────────────────────────────────
# Вспомогалки
# ──────────────────────────────────────────────────────────────────────────────
NBSP_RX = re.compile(r"[\u00A0\u202F]")

def _clean_text(s: str) -> str:
    s = (s or "").strip()
    s = NBSP_RX.sub(" ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s*\n\s*", " ", s)
    return s.strip()


def _digits(text: str) -> Optional[int]:
    s = re.sub(r"[^\d]", "", text or "")
    return int(s) if s else None


def _scroll(driver, steps: int = 36, dy: int = 900, slow: bool = False) -> None:
    for _ in range(steps):
        try:
            driver.execute_script(f"window.scrollBy(0,{dy});")
        except Exception:
            pass
        if slow:
            time.sleep(0.15)


def _try_click_tab(driver, label: str) -> None:
    """Аккуратно кликаем по вкладке, чтобы прогрузился её контент."""
    XPATHS = [
        f"//*[contains(@text, '{label}')]",                   # нестандартный атрибут text=...
        f"//*[self::button or self::div or self::span][contains(translate(., 'ПРИМЕНЕНИЕДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ',"
        f"'применениедополнительная информация'), '{label.lower()}')]",
    ]
    for xp in XPATHS:
        try:
            el = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, xp)))
            el.click()
            time.sleep(0.05)
            return
        except Exception:
            continue


def _find_price(soup: BeautifulSoup) -> str:
    # 1) meta[itemprop=price]
    meta = soup.select_one("[itemprop='price'][content]")
    if meta and meta.get("content"):
        return _clean_text(str(meta["content"]))
    # 2) видимый «25 720 ₽»
    m = re.search(r"(\d[\d \u00A0\u202F]{1,})\s*₽", soup.get_text(" ", strip=True))
    if m:
        return _clean_text(m.group(1).replace("\u00A0", " ").replace("\u202F", " "))
    # 3) любые большие числа в «price»-блоках
    for el in soup.select("[class*='price'], .price, [data-qa*='price']"):
        val = _digits(el.get_text(strip=True))
        if val:
            return str(val)
    return ""


def _find_rating(soup: BeautifulSoup) -> str:
    meta = soup.select_one("meta[itemprop='ratingValue'][content], [itemprop='ratingValue'][content]")
    if meta and meta.get("content"):
        return _clean_text(str(meta["content"]))
    # видимый «оценка товара 4.6»
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"(?:оценка\s+товара|рейтинг).*?([0-5](?:[.,]\d)?)", txt, flags=re.I)
    if m:
        return _clean_text(m.group(1).replace(",", "."))
    # просто первое число 0–5.x в блоках рейтинга
    for el in soup.select("[class*='rating'], [id*='rating']"):
        m = re.search(r"([0-5](?:[.,]\d)?)", el.get_text(" ", strip=True))
        if m:
            return _clean_text(m.group(1).replace(",", "."))
    return ""


def _find_name(soup: BeautifulSoup) -> str:
    el = soup.select_one("[itemprop='name']")
    if el:
        return _clean_text(el.get_text(" ", strip=True))
    # запасной вариант: крупный заголовок рядом с ценой/кнопкой
    for sel in ["h1", "h2", "header h1", "header h2", "div[class*='title'] span"]:
        tag = soup.select_one(sel)
        if tag:
            t = _clean_text(tag.get_text(" ", strip=True))
            if len(t) >= 3:
                return t
    return ""


def _find_description(soup: BeautifulSoup) -> str:
    el = soup.select_one("[itemprop='description'], .description [itemprop='description']")
    if el:
        return _clean_text(el.get_text(" ", strip=True))
    # в Gold Apple часто описание — первый .vSCKP под заголовком «Описание»
    for hdr in soup.find_all(string=re.compile(r"описан", re.I)):
        box = soup.find("div", class_=re.compile(r"vSCKP"))
        if box:
            return _clean_text(box.get_text(" ", strip=True))
    # иначе берём самый длинный абзац на странице (осторожно)
    paras = sorted((p.get_text(" ", strip=True) for p in soup.find_all("p")), key=len, reverse=True)
    return _clean_text(paras[0]) if paras else ""


def _find_after_label_block(soup: BeautifulSoup, label_rx: re.Pattern) -> str:
    """
    Ищем ближайший «контентный» блок (.vSCKP) после заголовка/вкладки с названием.
    Работает для «Применение», «Дополнительная информация» и т.п.
    """
    # 1) тэги со значением в нестандартном атрибуте text="Применение"
    for tag in soup.select("[text]"):
        txt = f"{tag.get('text','')}".strip()
        if label_rx.search(txt):
            box = tag.find_next("div", class_=re.compile(r"vSCKP"))
            if box:
                return _clean_text(box.get_text(" ", strip=True))

    # 2) обычный текст узла
    for tag in soup.find_all(text=label_rx):
        box = tag.find_parent().find_next("div", class_=re.compile(r"vSCKP"))
        if box:
            return _clean_text(box.get_text(" ", strip=True))

    return ""


def _extract_country_from_block(raw: str) -> str:
    """
    В «Доп. информации» встречаются строки:
    «Страна происхождения [НЛ] США [НЛ][НЛ] изготовитель: ...»
    Берём токен после «Страна происхождения».
    """
    text = _clean_text(raw)
    # сначала попробуем аккуратный разбор по токенам
    tokens = [t for t in re.split(r"[;•\|]|\s{2,}", text) if t]
    for i, t in enumerate(tokens):
        if re.search(r"страна\s*происхожд", t, flags=re.I):
            if i + 1 < len(tokens):
                cand = tokens[i + 1]
                # отсекаем возможный «изготовитель»
                if not re.search(r"изготовител", cand, flags=re.I):
                    return cand

    # фолбэк — regex «после двоеточия/после слова»
    m = re.search(r"страна\s*происхожд[а-я]*[:\s]+([A-Za-zА-Яа-яЁё \-]+)", text, flags=re.I)
    return _clean_text(m.group(1)) if m else ""


# ──────────────────────────────────────────────────────────────────────────────
# Парсинг карточки
# ──────────────────────────────────────────────────────────────────────────────
def parse_product(driver, url: str, slow: bool = False) -> GAProduct:
    driver.get(url)
    WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

    # Принудительно «трогаем» вкладки, чтобы контент гарантированно оказался в DOM
    for tab in ("Применение", "Дополнительная информация"):
        _try_click_tab(driver, tab)
        if slow:
            time.sleep(0.05)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    name = _find_name(soup)
    price = _find_price(soup)
    rating = _find_rating(soup)
    description = _find_description(soup)

    # Применение
    instructions = _find_after_label_block(soup, re.compile(r"применени", re.I))

    # Доп.инфо → страна
    add_info = _find_after_label_block(soup, re.compile(r"дополнител.*информац", re.I))
    country = _extract_country_from_block(add_info) if add_info else ""

    return GAProduct(
        url=url,
        name=name,
        price=price,
        rating=rating,
        description=description,
        instructions=instructions,
        country=country,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Парсинг листинга и общий поиск
# ──────────────────────────────────────────────────────────────────────────────
def _collect_links_from_listing_html(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    hrefs: List[str] = []
    seen = set()

    # 1) основной признак карточки
    for a in soup.select("a[data-transaction-name*='product-card']"):
        href = a.get("href") or a.get("data-href") or ""
        if not href:
            continue
        full = urljoin(BASE, href)
        if full not in seen:
            seen.add(full)
            hrefs.append(full)

    # 2) подстраховка по паттернам URL
    if not hrefs:
        for a in soup.select("a[href]"):
            href = a.get("href") or ""
            if not href:
                continue
            full = urljoin(BASE, href)
            if re.search(r"/\d{6,}-", full) or "/product/" in full:
                if full not in seen:
                    seen.add(full)
                    hrefs.append(full)

    return hrefs


def _collect_links_dom(driver) -> List[str]:
    seen = set()
    out: List[str] = []
    for sel in [
        "a[data-transaction-name*='product-card']",
        "a[href*='/product/']",
        "a[href*='/catalog/']",
    ]:
        try:
            anchors = driver.find_elements(By.CSS_SELECTOR, sel)
        except Exception:
            anchors = []
        for a in anchors:
            try:
                href = a.get_attribute("href") or a.get_attribute("data-href") or ""
                if not href:
                    continue
                full = urljoin(BASE, href)
                if full not in seen:
                    seen.add(full)
                    out.append(full)
            except Exception:
                continue
    return out


def search_goldapple(mode: str = "real", *, slow: bool = False, limit: int = 100) -> List[GAProduct]:
    """
    Возвращает список GAProduct из раздела «Парфюмерия».
    """
    products: List[GAProduct] = []

    if mode == "mock":
        # Для тестов подсовывайте локальные HTML
        from pathlib import Path
        lst = Path("tests/data/ga_listing_sample.html").read_text(encoding="utf-8")
        urls = _collect_links_from_listing_html(lst)[:min(limit, 10)]
        # Сопоставьте своим мок-страницам карточек
        for i, u in enumerate(urls):
            html = Path(f"tests/data/ga_product_sample_{i+1}.html").read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "html.parser")
            # «Парсим как в real», но без Selenium
            name = _find_name(soup)
            price = _find_price(soup)
            rating = _find_rating(soup)
            description = _find_description(soup)
            instructions = _find_after_label_block(soup, re.compile(r"применени", re.I))
            add_info = _find_after_label_block(soup, re.compile(r"дополнител.*информац", re.I))
            country = _extract_country_from_block(add_info) if add_info else ""
            products.append(GAProduct(u, name, price, rating, description, instructions, country))
        return products

    # REAL
    driver = get_selenium_driver(site="goldapple", headless=False)
    try:
        driver.get(SECTION)
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        _scroll(driver, steps=42, dy=1100, slow=slow)

        listing_html = driver.page_source
        urls = _collect_links_from_listing_html(listing_html)
        if not urls:
            urls = _collect_links_dom(driver)

        # safety-лимит
        urls = urls[:limit]

        for u in urls:
            try:
                prod = parse_product(driver, u, slow=slow)
                products.append(prod)
                if slow:
                    time.sleep(0.12)
            except Exception:
                continue

        return products
    finally:
        try:
            driver.quit()
        except Exception:
            pass



