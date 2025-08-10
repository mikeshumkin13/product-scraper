from __future__ import annotations

from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.selenium_driver import get_selenium_driver
from utils.selenium_helpers import load_site_cookies, human_sleep
from .base import Product
from .mock_parser import parse_mock_json


def search_wildberries(
    query: str,
    mode: str = "real",
    *,
    slow: bool = False,
    use_profile: bool = False,
    profile_dir: str | None = None,
) -> List[Product]:
    """
    Парсит Wildberries:
    - В режиме 'real' — через undetected_chromedriver (+куки, +профиль).
    - В режиме 'mock' — из JSON mock-файла.

    :param query: поисковый запрос
    :param mode: 'real' или 'mock'
    :param slow: «человеческие» задержки между шагами
    :param use_profile: использовать ли реальный профиль Chrome
    :param profile_dir: путь к каталогу профиля Chrome
    :return: список Product
    """
    if mode == "mock":
        return _parse_mock(query)

    base = "https://www.wildberries.ru/"
    url = f"{base}catalog/0/search.aspx?search={query}"

    driver = None
    try:
        driver = get_selenium_driver(site="wildberries", use_profile=use_profile, profile_dir=profile_dir)
        load_site_cookies(driver, "wildberries", base)
        human_sleep(slow)

        driver.get(url)
        human_sleep(slow)

        # ждём, пока появится контейнер с карточками (Wildberries часто меняет разметку)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "div[data-catalog-content] article, article.product-card, div.product-card"
        )))

        # сохраняем html для отладки
        Path("tests/wb_real.html").write_text(driver.page_source, encoding="utf-8")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # несколько вариантов карточек (страницы WB бывают разными)
        cards = (
            soup.select("div[data-catalog-content] article") or
            soup.select("article.product-card") or
            soup.select("div.product-card")
        )

        products: List[Product] = []
        for card in cards[:20]:
            try:
                # имя
                name_tag = (
                    card.select_one("span.goods-name") or
                    card.select_one("[data-link*='name']") or
                    card.select_one("a[aria-label]")
                )
                if not name_tag:
                    continue
                name = (name_tag.get_text(strip=True) if name_tag.name != "a"
                        else (name_tag.get("aria-label") or name_tag.get_text(strip=True)))
                if not name:
                    continue

                # ссылка
                a = card.select_one("a[href]")
                href = a.get("href") if a else ""
                if href and not href.startswith("http"):
                    href = base.rstrip("/") + href

                # цена (пробуем несколько селекторов)
                price_el = (
                    card.select_one("ins.price__lower-price") or
                    card.select_one("span.lower-price") or
                    card.select_one("span.price") or
                    card.select_one("p.price")
                )
                price_text = price_el.get_text(strip=True) if price_el else ""
                digits = "".join(ch for ch in price_text if ch.isdigit())
                price = int(digits) if digits else "Нет цены"

                products.append(Product(name=name, url=href or base, price=price))
            except Exception:
                continue

        # укорачиваем до 10 и убираем дубли
        uniq, seen = [], set()
        for p in products:
            k = (p.name, p.url)
            if k not in seen:
                uniq.append(p)
                seen.add(k)
            if len(uniq) == 10:
                break

        return uniq if uniq else _fb(query, "пусто/селекторы")

    except Exception as e:
        return _fb(query, f"исключение: {e}")
    finally:
        if driver:
            driver.quit()


def _parse_mock(query: str) -> List[Product]:
    """
    Парсит локальный mock JSON для Wildberries.
    Ожидается массив объектов: [{"name": "...","price": 12345,"url": "..."}]
    """
    path = Path("src/parser/mock/wildberries_mock.json")
    if not path.exists():
        return []

    data = path.read_text(encoding="utf-8")
    return parse_mock_json(data, query)


def _fb(query: str, reason: str) -> List[Product]:
    print(f"🔁 WILDBERRIES: фолбэк на mock ({reason})")
    return _parse_mock(query)


