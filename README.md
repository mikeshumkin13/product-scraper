# 📘 Product Scraper

**Дипломный проект Skypro (BB1)**  
Веб-скрапинг информации о товарах с сайтов. 
(на примере [books.toscrape.com](https://books.toscrape.com)).

## 📦 Возможности

- Сбор информации о товарах (название, цена, ссылка)
- Экспорт результатов в CSV-файл
- Запуск через командную строку (CLI)
- Гибкое указание URL и имени файла
- Покрытие юнит-тестами
- Стиль кода PEP8, OOP, Regex

## 🚀 Установка и запуск

1. Клонируй репозиторий и перейди в папку проекта:

git clone git@github.com:mikeshumkin13/product-scraper.git
cd product-scraper

2. Установи зависимости через Poetry:
poetry install

3. Запусти парсинг:
poetry run python src/main.py --url "https://books.toscrape.com/catalogue/category/books/science_22/index.html" --output result.csv


Запуск тестов.

poetry run pytest


# Технологии:
Python 3.12

Poetry

Requests, BeautifulSoup4

CSV, Regex

Pytest

Git, GitHub, GitFlow

🔖 Теги из ТЗ
✅ git — используется

✅ pep8 — flake8 + black

✅ readme — ✅

✅ tests — покрытие на парсер и экспорт

✅ OOP — реализован через BaseParser + BooksParser

✅ parser — основной модуль

✅ csv — экспорт данных

✅ regex — извлечение цен

