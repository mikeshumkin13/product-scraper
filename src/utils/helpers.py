from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver


def human_sleep(min_s: float = 0.8, max_s: float = 1.6, slow: bool = False) -> None:
    """
    Небольшая случайная пауза. В режиме slow — длиннее.
    """
    k = 2.5 if slow else 1.0
    dt = random.uniform(min_s, max_s) * k
    time.sleep(dt)


def load_site_cookies(
    driver: WebDriver, cookies_file: str | Path, base_url: str
) -> None:
    """
    Загружает cookies из JSON (список словарей в формате Chrome DevTools).
    Перед добавлением cookie обязательно открыть домен base_url.
    """
    p = Path(cookies_file)
    if not p.exists():
        return

    # Chrome/Firefox требуют сначала зайти на домен
    driver.get(base_url)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return

    for c in data:
        # приведение ключей к формату Selenium
        cookie = {
            "name": c.get("name"),
            "value": c.get("value"),
            "path": c.get("path", "/"),
            "domain": c.get("domain"),
            "secure": bool(c.get("secure", False)),
            "httpOnly": bool(c.get("httpOnly", False)),
        }
        # expiry должен быть int/None
        if "expiry" in c and isinstance(c["expiry"], (int, float)):
            cookie["expiry"] = int(c["expiry"])
        try:
            driver.add_cookie(cookie)
        except Exception:
            # пропускаем кривые/чужие куки
            pass
