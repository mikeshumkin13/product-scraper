# 🛍️ Product Scraper (BB1) — Веб скрапинг информации о товарах.


**Диплом SkyPro, тема BB1** — сбор товаров по запросу с **DNS, Citilink, Wildberries, Ozon** с выгрузкой в единый CSV.  
Поддержаны режимы **real (Selenium)** и **mock** (офлайн), **фолбэк** на mock при сбоях, и **Telegram‑бот**, который принимает запрос и присылает CSV прямо в чат.

---

## ⚙️ Возможности

- 4 источника: DNS, Citilink, Wildberries, Ozon
- **undetected‑chromedriver** (Chrome) + опции для «human‑поведения»; поддержан Firefox (geckodriver)
- Подгрузка **cookies** и (опционально) **реального профиля** браузера
- Ozon: гибрид DOM → **composer‑API** для деталей карточки
- **Единая схема данных**: `name, price, currency, url, image`
- **Фолбэк**: при падении парсера сайт переключается на mock‑режим
- **CSV UTF‑8 BOM** — корректное открытие в Excel
- **Тесты** (`pytest`) — mock/real пути, проверка CSV и фолбэка
- **Telegram‑бот** — ввод запроса → CSV в ответ

---

## 🧱 Стек

- Python **3.12**
- Selenium, **undetected‑chromedriver**, BeautifulSoup4
- curl_cffi (Ozon composer‑API)
- pytest
- python‑telegram‑bot 21.x
- Poetry

---

## 📦 Установка

git clone https://github.com/mikeshumkin13/product-scraper.git
cd product-scraper
poetry install

Создайте .env (можно скопировать из .env.example):
# Telegram
PS_BOT_TOKEN=PUT_YOUR_TOKEN_HERE

# Scraper defaults
PS_BROWSER=chrome          # chrome|firefox
PS_MODE=real               # real|mock
PS_SLOW=1                  # 1=humanize задержки, 0=выкл
PS_USE_PROFILE=0           # 1=использовать реальный профиль
PS_PROFILE_DIR=            # путь к профилю (опц.)

# Telegram network tuning (по умолчанию ок)
TG_HTTP_VERSION=1.1
TG_CONNECT_TIMEOUT=5
TG_READ_TIMEOUT=30
TG_WRITE_TIMEOUT=30
TG_POOL_TIMEOUT=5
# TG_PROXY_URL=           # если нужен прокси (http://user:pass@host:port)

macOS: для Firefox поставьте geckodriver — brew install geckodriver.

# ▶️ Быстрый старт (CLI)

Реальный запуск (Chrome/UDC):
PS_BROWSER=chrome poetry run python src/main.py \
  --query "чайник" \
  --mode real \
  --slow \
  --output real_kettle.csv

# Офлайн‑мок:
poetry run python src/main.py --query "чайник" --mode mock --output test_mock.csv


Параметры CLI:

--mode {real,mock} — режим работы

--query — поисковый запрос

--output — путь к CSV

--slow — «человеческие» задержки (1–3 сек) и мягкий скролл

--profile — использовать реальный профиль Chrome/Firefox

--profile-dir — путь к профилю


# 🤖 Telegram‑бот
 ## @productscraper_bot
Запуск:

poetry run python src/bot.py


Команды в чате:

/start — помощь

/mock — режим mock

/real — режим real

Как пользоваться: отправьте боту слово, например пылесос.
Бот запустит парсер и пришлёт CSV файл прямо в чат.

Бот требует .env c PS_BOT_TOKEN. Если Telegram недоступен, бот вежливо сообщит и предложит /mock.


# 🧪 Тесты

Запуск всех тестов:

poetry run pytest -q

Ожидаемо: 9 passed.
Тесты покрывают:

- формирование CSV и кодировку UTF‑8 BOM;

- парсинг mock‑данных со всех сайтов;

- фолбэк на mock при ошибке real;

- запуск run_searches в mock‑режиме.


# 🧰 Структура проекта

src/
├── main.py                     # CLI-оркестратор
├── bot.py                      # Telegram-бот (по запросу -> CSV)
├── auth/
│   ├── cookies/*.json          # куки для сайтов
│   └── ozon_profile/           # пример профиля Chrome (опц.)
├── parser/
│   ├── base.py                 # базовые сущности (OOP)
│   ├── dns_search.py           # DNS
│   ├── citilink_search.py      # Citilink
│   ├── wildberries_search.py   # Wildberries (DOM + soup)
│   └── ozon_search.py          # Ozon (DOM -> composer-API)
│   └── mock/                   # mock-данные для офлайна
└── utils/
    ├── selenium_driver.py      # undetected-chromedriver, Firefox, профили
    ├── helpers.py              # human_sleep, cookies loader
    ├── user_agents.py
    └── csv_export.py           # экспорт CSV (UTF-8 BOM)


# 🧹 Стиль кода (PEP8)

Мы придерживаемся PEP8, рекомендуемый линтер — flake8 (лимит 119 символов).
Добавьте в локальную проверку:

poetry add --group dev flake8
poetry run flake8 src tests

# 🛡️ Фолбэк и устойчивость

Каждый парсер обёрнут в try/except; при проблемах сайт уходит в mock.

Wildberries/DNS сохраняют html для отладки: tests/wb_real.html, tests/dns_real.html.

Ozon использует cookies из Selenium‑сессии для composer‑API.

# 📄 Формат CSV

name,price,currency,url,image
— Пустые поля допустимы, экспорт устойчив к dict и dataclass.
— Кодировка: UTF‑8 with BOM — открывается в Excel без «кракозябр».

# 🧭 GitFlow

main — стабильные релизы

develop — активная разработка

feature/*, fix/*, docs/* — фичи/фиксы/документация

PR → develop, code review, squash‑merge


# 📚 Теги ТЗ (обязательные)

Git, PEP8, Readme, Tests, OOP, Parser, CSV, Regex — выполнены.

# 🧭 Дорожная карта (грандиозные планы по расширению функционала проекта и продаже после защиты диплома))

История цен и графики (по запросам/товарам)

Уведомления о снижении цены (подписки через бота)

Сравнение площадок, выделение лучшей цены

Фильтры/категории, /top N, /sort price_asc|desc

Экспорт в Google Sheets, PDF‑отчёты

API и B2B‑тарифы



# 👤 Автор

GitHub: https://github.com/mikeshumkin13


