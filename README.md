# 🛍️ Product Scraper (BB1) — Веб скрапинг информации о товарах.

**Диплом SkyPro, тема BB1** — сбор товаров по запросу с **DNS, Citilink, Wildberries, Ozon** с выгрузкой в единый CSV.  
Поддержаны режимы **real (Selenium)** и **mock** (офлайн), **фолбэк** на mock при сбоях, и **Telegram-бот**, который принимает запрос и присылает CSV прямо в чат.

> 🆕 **Gold Apple — Парфюмерия.** Отдельный модуль, который собирает **до 100** карточек с полями:  
> `url, name, price, rating, description, instructions, country` и сохраняет в `goldapple_perfume.csv`.

---

## ⚙️ Возможности

- 4 источника: DNS, Citilink, Wildberries, Ozon
- **undetected-chromedriver** (Chrome) + опции для «human-поведения»; поддержан Firefox (geckodriver)
- Подгрузка **cookies** и (опционально) **реального профиля** браузера
- Ozon: гибрид DOM → **composer-API** для деталей карточки
- **Единая схема данных**: `name, price, currency, url, image`
- **Фолбэк**: при падении парсера сайт переключается на mock-режим
- ~~**CSV UTF-8 BOM** — корректное открытие в Excel~~  
  **CSV UTF-8** по умолчанию (для юнит-тестов). Excel открывает корректно; при необходимости BOM можно вернуть.
- **Тесты** (`pytest`) — mock/real пути, проверка CSV и фолбэка
- **Telegram-бот** — ввод запроса → CSV в ответ

> 🆕 **Gold Apple (Парфюмерия)**  
> - Стабильная навигация по категории + сбор ссылок (пагинация `?p=...` и fallback на бесконечный скролл).  
> - Эвристики + регулярные выражения для цены/рейтинга/страны.  
> - Нормализация и «умное» укорачивание описаний/инструкций (до 200 символов).  
> - Мягкие клики по вкладкам **Описание/Применение/Бренд/Доп. информация**.

---

## 🧱 Стек

- Python **3.12**
- Selenium, **undetected-chromedriver**, BeautifulSoup4
- curl_cffi (Ozon composer-API)
- pytest (**+ pytest-cov**)
- python-telegram-bot 21.x
- Poetry

---

## 📦 Установка

git clone https://github.com/mikeshumkin13/product-scraper.git
cd product-scraper
poetry install

## Создайте .env (можно скопировать из .env.example):
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
TG_PROXY_URL=           # если нужен прокси (http://user:pass@host:port)

macOS: для Firefox поставьте geckodriver — brew install geckodriver.

## Быстрый старт (CLI)

Реальный запуск (Chrome/UDC):

PS_BROWSER=chrome poetry run python src/main.py \
  --query "чайник" \
  --mode real \
  --slow \
  --output real_kettle.csv

Офлайн-мок:

poetry run python src/main.py --query "чайник" --mode mock --output test_mock.csv

Параметры CLI:

--mode {real,mock} — режим работы

--query — поисковый запрос

--output — путь к CSV

--slow — «человеческие» задержки (1–3 сек) и мягкий скролл

--profile — использовать реальный профиль Chrome/Firefox

--profile-dir — путь к профилю

## Gold Apple — Парфюмерия → CSV

Собираем товары из раздела «Парфюмерия» с полями:
url, name, price, rating, description, instructions, country.

Запуск:
poetry run python src/goldapple_main.py --mode real --limit 100 --slow --output goldapple_perfume.csv

# goldapple_perfume.csv 
- сохранён в корне проекта. 

## Telegram-бот

@productscraper_bot

Запуск:

poetry run python src/bot.py


Команды в чате:

/start — помощь

/mock — режим mock

/real — режим real

Как пользоваться: отправьте боту слово, например пылесос.
Бот запустит парсер и пришлёт CSV файл прямо в чат.
Бот требует .env с PS_BOT_TOKEN. Если Telegram недоступен, бот вежливо сообщит и предложит /mock.

## Тесты

Запуск всех тестов:

poetry run pytest -q

### тесты по Galdapple 

pytest -q -m goldapple --cov --cov-report=term-missing --cov-fail-under=75
...........                                                                                                                                                                                                 [100%]
================================================================================================= tests coverage ==================================================================================================
________________________________________________________________________________ coverage: platform darwin, python 3.12.4-final-0 _________________________________________________________________________________

Name                             Stmts   Miss Branch BrPart  Cover   Missing
----------------------------------------------------------------------------
src/parser/constants.py             12      0      0      0   100%
src/parser/entities.py              11      0      0      0   100%
src/parser/goldapple_search.py      16      2      0      0    88%   448-449
src/utils/text_utils.py             27      7     10      4    65%   11, 27, 30, 34-37
----------------------------------------------------------------------------
TOTAL                               66      9     10      4    80%
Required test coverage of 75% reached. Total coverage: 80.26%
11 passed, 16 deselected in 2.89s



## Структура проекта

src/
├── main.py                     # CLI-оркестратор
├── goldapple_main.py           # CLI: Gold Apple → CSV
├── bot.py                      # Telegram-бот (по запросу -> CSV)
├── auth/
│   ├── cookies/*.json          # куки для сайтов
│   └── ozon_profile/           # пример профиля Chrome (опц.)
├── parser/
│   ├── base.py                 # базовые сущности (OOP)
│   ├── dns_search.py           # DNS
│   ├── citilink_search.py      # Citilink
│   ├── wildberries_search.py   # Wildberries (DOM + soup)
│   ├── ozon_search.py          # Ozon (DOM -> composer-API)
│   ├── goldapple_search.py     # Gold Apple (Парфюмерия)
│   ├── entities.py             # GAProduct dataclass
│   ├── constants.py            # константы/таймауты/страны
│   └── mock/                   # mock-данные для офлайна
└── utils/
    ├── selenium_driver.py      # undetected-chromedriver, Firefox, профили
    ├── helpers.py              # human_sleep, cookies loader
    ├── user_agents.py
    ├── csv_export.py           # экспорт CSV (UTF-8)
    └── text_utils.py           # clean_text/shorten_text/digits


## Стиль кода (PEP8)

Мы придерживаемся PEP8, рекомендуемый линтер — flake8 (лимит 119 символов).
Добавьте в локальную проверку:

poetry add --group dev flake8
poetry run flake8 src tests

## Фолбэк и устойчивость

Каждый парсер обёрнут в try/except; при проблемах сайт уходит в mock.
Wildberries/DNS сохраняют html для отладки: tests/wb_real.html, tests/dns_real.html.
Ozon использует cookies из Selenium-сессии для composer-API.

## Форматы CSV
Общий CSV (4 магазина)
name, price, currency, url, image

Gold Apple (Парфюмерия)

url, name, price, rating, description, instructions, country

Кодировка: UTF-8

## GitFlow

main — стабильные релизы

develop — активная разработка

feature/*, fix/*, docs/* — фичи/фиксы/документация

PR → develop, code review, squash-merge

## Теги ТЗ (обязательные)

Git, PEP8, Readme, Tests, OOP, Parser, CSV, Regex — выполнены.
Gold Apple (Парфюмерия) — реализовано по ТЗ.

## Дорожная карта

- История цен и графики (по запросам/товарам)
- Уведомления о снижении цены (подписки через бота)
- Сравнение площадок, выделение лучшей цены
- Фильтры/категории, /top N, /sort price_asc|desc
- Экспорт в Google Sheets, PDF-отчёты
- API и B2B-тарифы

## 👤 Автор

GitHub: https://github.com/mikeshumkin13


