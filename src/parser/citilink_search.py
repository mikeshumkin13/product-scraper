from __future__ import annotations

import re
import time
from typing import List, Dict, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.selenium_driver import get_selenium_driver


BASE = "https://www.citilink.ru"


def _digits(text: str) -> Optional[int]:
    s = re.sub(r"[^\d]", "", text or "")
    return int(s) if s else None


def _slow(slow: bool, t: float = 0.2) -> None:
    if slow:
        time.sleep(t)


def search_citilink(
    query: str,
    mode: str,
    *,
    slow: bool = False,
    use_profile: bool = False,
    profile_dir: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Текущая разметка (см. скрины):
      — ссылки карточек имеют класс вида `app-catalog-*-Anchor` и href начинается с `/product/`
      — цена находится в span внутри карточки; берём первое число из всех span’ов-кандидатов
    Подход: находим все anchor'ы с `/product/`, из родителя вытягиваем цену.
    """

    if mode == "mock":
        # Лёгкий фиктивный набор для тестов
        return [
            {
                "name": "Чайник электрический MOCK A",
                "price": "1990",
                "rating": "4.6",
                "url": "https://www.citilink.ru/product/mock-a/",
                "image": "https://example.com/mock-a.jpg",
            },
            {
                "name": "Чайник электрический MOCK B",
                "price": "2490",
                "rating": "4.7",
                "url": "https://www.citilink.ru/product/mock-b/",
                "image": "https://example.com/mock-b.jpg",
            },
        ]

    url = f"{BASE}/search/?text={query}"
    driver = get_selenium_driver(
        site="citilink",
        headless=False,
        use_profile=use_profile,
        profile_dir=profile_dir,
    )

    try:
        driver.get(url)

        # ждём появление плитки
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "main"))
        )

        # скроллим страницу, чтобы догрузить побольше карточек
        for _ in range(20):
            driver.execute_script("window.scrollBy(0, 900);")
            _slow(slow, 0.15)

        # собираем ссылки на карточки
        anchors = driver.find_elements(
            By.CSS_SELECTOR, 'a[class*="Anchor"][href^="/product/"]'
        )
        results: List[Dict[str, str]] = []

        seen = set()
        for a in anchors:
            try:
                href = a.get_attribute("href")
                if not href or href in seen:
                    continue
                seen.add(href)

                # название есть в title у anchor, иначе — видимый текст
                name = (a.get_attribute("title") or a.text or "").strip()
                if not name:
                    # иногда текст в дочерних блоках
                    name = a.get_attribute("aria-label") or ""

                # ищем ближайшую цену в пределах карточки (родителя)
                card = a
                # поднимаемся к ближайшему карточному контейнеру
                for _ in range(4):
                    card = card.find_element(By.XPATH, "./..")

                spans = card.find_elements(By.TAG_NAME, "span")
                price_int: Optional[int] = None
                for sp in spans:
                    txt = sp.text.strip()
                    val = _digits(txt)
                    if val:
                        # отфильтруем неценовые крошки, берём первую реалистичную (>100)
                        if val > 100:
                            price_int = val
                            break

                results.append(
                    {
                        "name": name,
                        "price": price_int if price_int is not None else "",
                        "url": href,
                    }
                )
                _slow(slow, 0.02)
            except Exception:
                continue

        return results[:10]  # ограничимся первыми 10
    finally:
        try:
            driver.quit()
        except Exception:
            pass
