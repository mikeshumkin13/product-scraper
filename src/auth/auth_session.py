import json
import os
from pathlib import Path
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = Path(__file__).resolve().parent
COOKIES_DIR = BASE_DIR / "cookies"
PROFILE_DIR = BASE_DIR / "ozon_profile"  # Одна папка на все сайты
COOKIES_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)

sites = {
    "ozon": {
        "url": "https://www.ozon.ru/",
        "file": "ozon_cookies.json",
    },
    "dns": {
        "url": "https://www.dns-shop.ru/",
        "file": "dns_cookies.json",
    },
    "citilink": {
        "url": "https://www.citilink.ru/",
        "file": "citilink_cookies.json",
    },
    "wildberries": {
        "url": "https://www.wildberries.ru/",
        "file": "wildberries_cookies.json",
    },
}


def save_cookies(site: str, url: str, file: str):
    print(f"\n🚀 Откроется браузер для авторизации на {url}")
    print("👉 Войди вручную в аккаунт. После входа не закрывай вкладку!")
    print(
        "⏳ После входа — подожди пару секунд и нажми Enter в терминале для сохранения cookies."
    )

    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)  # НЕ закрывать вкладку

    # 🧠 Маскировка Selenium
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)

    input("📥 Нажми Enter, чтобы сохранить cookies...")

    cookies = driver.get_cookies()
    with open(COOKIES_DIR / file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)

    print(f"✅ Cookies для {site} сохранены в {COOKIES_DIR / file}")
    # Не закрываем браузер, но отключим драйвер
    driver.quit()


if __name__ == "__main__":
    print("📋 Доступные сайты:")
    for s in sites:
        print(f"- {s}")
    selected = (
        input("🔎 Введи название сайта (ozon / dns / citilink / wildberries): ")
        .strip()
        .lower()
    )

    if selected in sites:
        save_cookies(
            site=selected, url=sites[selected]["url"], file=sites[selected]["file"]
        )
    else:
        print("❌ Неверный сайт.")
