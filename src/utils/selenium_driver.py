from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import undetected_chromedriver as uc


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)


def _get_chrome_major_mac() -> Optional[int]:
    """
    Возвращает major-версию установленного Chrome на macOS (например, 138).
    """
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                out = subprocess.check_output([path, "--version"], text=True).strip()
                m = re.search(r"(\d+)\.", out)
                if m:
                    return int(m.group(1))
            except Exception:
                pass
    # запасной вариант (если вдруг есть бинарь в PATH)
    try:
        out = subprocess.check_output(["/usr/bin/env", "google-chrome", "--version"], text=True).strip()
        m = re.search(r"(\d+)\.", out)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def get_selenium_driver(
    site: str = "",
    *,
    headless: bool = False,
    use_profile: bool = False,
    profile_dir: Optional[str] = None,
) -> uc.Chrome:
    """
    Создаёт undetected‑chromedriver с защитой от детекта и, при желании, с реальным профилем.
    Ставит chromedriver, совместимый с текущей версией Chrome (через version_main).
    """
    options = uc.ChromeOptions()

    # Профиль
    if use_profile:
        if not profile_dir:
            # системный каталог профилей Chrome (а не сам Default-профиль)
            profile_dir = str(Path.home() / "Library/Application Support/Google/Chrome")
        options.add_argument(f"--user-data-dir={profile_dir}")
        # если есть профиль Default — явно укажем
        default_profile = Path(profile_dir) / "Default"
        if default_profile.is_dir():
            options.add_argument("--profile-directory=Default")

    # Базовые флаги
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-features=AutomationControlled,PrivacySandboxSettings3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1280,900")
    options.add_argument(f"--user-agent={DEFAULT_USER_AGENT}")

    version_main = _get_chrome_major_mac()  # напр.: 138 → UDC качнёт совместимый драйвер

    driver = uc.Chrome(
        options=options,
        headless=headless,
        version_main=version_main,
        # browser_executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # опционально
    )
    return driver


