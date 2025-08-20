from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import undetected_chromedriver as uc
from selenium import webdriver as _wd
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/139.0.0.0 Safari/537.36"
)


def _apply_profile_chrome(
    options: uc.ChromeOptions, use_profile: bool, profile_dir: Optional[str]
) -> None:
    if not use_profile:
        return
    if not profile_dir:
        profile_dir = str(Path.home() / "Library/Application Support/Google/Chrome")
    options.add_argument(f"--user-data-dir={profile_dir}")
    default_profile = Path(profile_dir) / "Default"
    if default_profile.is_dir():
        options.add_argument("--profile-directory=Default")


def _make_chrome(headless: bool, use_profile: bool, profile_dir: Optional[str]):
    options = uc.ChromeOptions()
    _apply_profile_chrome(options, use_profile, profile_dir)

    # быстрее: не ждём загрузки картинок/рекламы
    try:
        options.page_load_strategy = "eager"
    except Exception:
        pass

    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-features=PrivacySandboxSettings3")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1280,900")
    options.add_argument(f"--user-agent={DEFAULT_USER_AGENT}")

    return uc.Chrome(options=options, headless=headless)


def _apply_profile_firefox(
    opts: FirefoxOptions, use_profile: bool, profile_dir: Optional[str]
) -> None:
    if not use_profile:
        return
    if not profile_dir:
        base = Path.home() / "Library/Application Support/Firefox/Profiles"
        candidates = list(base.glob("*.default*"))
        if candidates:
            profile_dir = str(candidates[0])
        else:
            return
    opts.set_preference("profile", profile_dir)


def _make_firefox(headless: bool, use_profile: bool, profile_dir: Optional[str]):
    opts = FirefoxOptions()
    try:
        opts.page_load_strategy = "eager"
    except Exception:
        pass

    if headless:
        opts.add_argument("-headless")
    opts.set_preference("dom.webdriver.enabled", False)
    opts.set_preference("useAutomationExtension", False)
    opts.set_preference("media.peerconnection.enabled", False)
    opts.set_preference("privacy.trackingprotection.enabled", True)
    _apply_profile_firefox(opts, use_profile, profile_dir)

    service = FirefoxService()
    driver = _wd.Firefox(service=service, options=opts)
    driver.set_window_size(1280, 900)
    return driver


def get_selenium_driver(
    site: str = "",
    *,
    headless: bool = False,
    use_profile: bool = False,
    profile_dir: Optional[str] = None,
    browser: Optional[str] = None,
):
    choice = (browser or os.getenv("PS_BROWSER") or "chrome").lower()
    if choice == "firefox":
        return _make_firefox(
            headless=headless, use_profile=use_profile, profile_dir=profile_dir
        )
    return _make_chrome(
        headless=headless, use_profile=use_profile, profile_dir=profile_dir
    )
