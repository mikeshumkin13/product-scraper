from __future__ import annotations
import json
import random
import time
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver

COOKIES_DIR = Path("src/auth/cookies")

SITE_COOKIES = {
    "ozon":        COOKIES_DIR / "ozon_cookies.json",
    "dns":         COOKIES_DIR / "dns_cookies.json",
    "citilink":    COOKIES_DIR / "citilink_cookies.json",
    "wildberries": COOKIES_DIR / "wildberries_cookies.json",
}


def human_sleep(slow: bool, min_s: float | None = None, max_s: float | None = None) -> None:
    """
    Спит «по‑человечески», если slow=True.
    Совместима с двумя способами вызова:
      human_sleep(slow)                           # старый стиль
      human_sleep(slow, min_s=0.6, max_s=1.2)     # новый стиль
    """
    if not slow:
        return

    # если min/max не заданы — используем мягкие дефолты
    if min_s is None and max_s is None:
        delay = random.uniform(0.6, 1.2)
    else:
        if min_s is None:
            min_s = 0.4
        if max_s is None:
            max_s = min_s
        delay = random.uniform(float(min_s), float(max_s))

    time.sleep(delay)




def load_site_cookies(driver: WebDriver, site: str, base_url: str) -> None:
    """Подливаем сохранённые cookies для домена и перегружаем страницу."""
    path = SITE_COOKIES.get(site)
    if not path or not path.exists():
        print(f"⚠️ Cookies для {site} не найдены ({path}). Пойдём без них.")
        return

    driver.get(base_url)
    data = json.loads(path.read_text(encoding="utf-8"))
    cookies = data["cookies"] if isinstance(data, dict) and "cookies" in data else data

    added = 0
    for ck in cookies:
        try:
            ck = {k: v for k, v in ck.items() if k in {
                "name", "value", "domain", "path", "expiry", "httpOnly", "secure", "sameSite"
            }}
            ck.setdefault("path", "/")
            driver.add_cookie(ck)
            added += 1
        except Exception:
            continue

    if added:
        driver.get(base_url)


