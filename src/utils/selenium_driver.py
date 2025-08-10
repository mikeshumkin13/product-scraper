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

# Стандартный путь к Chrome на macOS
MAC_CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _detect_chrome_binary() -> Optional[str]:
    """Возвращает путь к бинарю Chrome на macOS, если найден."""
    candidates = [
        MAC_CHROME_BIN,
        "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # запасной вариант: вдруг доступен в PATH
    for name in ("google-chrome", "chromium", "chrome"):
        try:
            p = subprocess.check_output(["/usr/bin/env", "which", name], text=True).strip()
            if p:
                return p
        except Exception:
            pass
    return None


def _get_chrome_major(binary_path: Optional[str]) -> Optional[int]:
    """Читает версию браузера и отдаёт major (напр., 139)."""
    if not binary_path:
        return None
    try:
        out = subprocess.check_output([binary_path, "--version"], text=True).strip()
        # Примеры: "Google Chrome 139.0.7258.67", "Chromium 119.0.6045.159"
        m = re.search(r"\b(\d+)\.", out)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def _normalize_profile_args(options: uc.ChromeOptions, use_profile: bool, profile_dir: Optional[str]) -> None:
    """
    Корректно добавляет аргументы профиля:
    - если передан путь до .../Chrome/Default → user-data-dir = .../Chrome + --profile-directory=Default
    - если передан путь до .../Chrome → просто user-data-dir
    """
    if not use_profile:
        return

    if not profile_dir:
        # системный каталог профилей Chrome (не сам профиль)
        profile_dir = str(Path.home() / "Library/Application Support/Google/Chrome")

    p = Path(profile_dir).expanduser()

    # Если нам дали .../Chrome/Default — используем родителя как user-data-dir и явно укажем профиль
    if p.name == "Default" and p.parent.name == "Chrome":
        options.add_argument(f"--user-data-dir={p.parent}")
        options.add_argument("--profile-directory=Default")
    else:
        # Иначе считаем, что это корень профилей (.../Chrome) или кастомный каталог
        options.add_argument(f"--user-data-dir={p}")
        default_profile = p / "Default"
        if default_profile.is_dir():
            options.add_argument("--profile-directory=Default")


def get_selenium_driver(
    site: str = "",
    *,
    headless: bool = False,
    use_profile: bool = False,
    profile_dir: Optional[str] = None,
) -> uc.Chrome:
    """
    Создаёт undetected‑chromedriver с защитой от детекта.
    - Подбирает chromedriver под текущий Chrome через version_main.
    - Корректно подключает профиль.
    """
    options = uc.ChromeOptions()

    # Профиль
    _normalize_profile_args(options, use_profile, profile_dir)

    # Базовые флаги (деликатные, без лишней палевы)
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

    # Небольшие антидетект-настройки
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    })

    # Определяем бинарь и версию Chrome
    chrome_bin = _detect_chrome_binary()
    version_main = _get_chrome_major(chrome_bin)

    # Если не смогли определить — разумный дефолт (на сегодня это 139)
    if version_main is None:
        version_main = 139

    # Стартуем UDC. use_subprocess=True повышает стабильность на macOS.
    driver = uc.Chrome(
        options=options,
        headless=headless,
        version_main=version_main,
        browser_executable_path=chrome_bin,
        use_subprocess=True,
    )

    return driver


