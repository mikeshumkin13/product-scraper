# src/main.py
from __future__ import annotations

import argparse
from typing import List

from utils.csv_export import export_to_csv
from parser.dns_search import search_dns
from parser.citilink_search import search_citilink
from parser.ozon_search import search_ozon
from parser.wildberries_search import search_wildberries
from parser.base import Product


def build_cli() -> argparse.ArgumentParser:
    """
    Создаёт и настраивает CLI-парсер аргументов.

    Флаги:
    - --mode: real|mock — режим работы.
    - --query: строка запроса.
    - --output: путь к CSV.
    - --slow: включить «человеческие» задержки (1–3 сек между шагами).
    - --profile: использовать реальный профиль Chrome (UDC + user-data-dir).
    - --profile-dir: путь к каталогу профиля Chrome (если не указан — системный Default на macOS).
    """
    parser = argparse.ArgumentParser(
        description="🛍 Product Scraper (UDC + cookies + profile)"
    )

    parser.add_argument(
        "--mode",
        choices=["real", "mock"],
        default="real",
        help="Режим работы: real (по умолчанию) или mock",
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Название товара для поиска (например: 'чайник')",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results.csv",
        help="Имя итогового CSV файла",
    )
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Добавить реалистичные задержки 1–3 сек между шагами",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Использовать реальный профиль Chrome (user-data-dir)",
    )
    parser.add_argument(
        "--profile-dir",
        type=str,
        default=None,
        help="Путь к каталогу профиля Chrome (если не указан — системный Default на macOS)",
    )
    return parser


def run_searches(
    query: str,
    mode: str,
    *,
    slow: bool,
    use_profile: bool,
    profile_dir: str | None,
) -> List[Product]:
    """
    Запускает парсинг по всем магазинам и собирает результаты.

    :param query: строка запроса
    :param mode: 'real' или 'mock'
    :param slow: включать ли задержки 1–3 сек между шагами
    :param use_profile: использовать ли реальный профиль Chrome
    :param profile_dir: путь к каталогу профиля (None — системный Default на macOS)
    :return: список объектов Product
    """
    all_products: List[Product] = []

    print(f"🔎 Ищем товары по запросу: {query}\n")

    # DNS
    try:
        dns_products = search_dns(
            query,
            mode=mode,
            slow=slow,
            use_profile=use_profile,
            profile_dir=profile_dir,
        )
        all_products.extend(dns_products)
        print(f"📦 DNS: найдено {len(dns_products)}")
    except Exception as e:
        print(f"❌ DNS: ошибка — {e}")

    # Citilink
    try:
        citilink_products = search_citilink(
            query,
            mode=mode,
            slow=slow,
            use_profile=use_profile,
            profile_dir=profile_dir,
        )
        all_products.extend(citilink_products)
        print(f"📦 Citilink: найдено {len(citilink_products)}")
    except Exception as e:
        print(f"❌ Citilink: ошибка — {e}")

    # Wildberries
    try:
        wb_products = search_wildberries(
            query,
            mode=mode,
            slow=slow,
            use_profile=use_profile,
            profile_dir=profile_dir,
        )
        all_products.extend(wb_products)
        print(f"📦 Wildberries: найдено {len(wb_products)}")
    except Exception as e:
        print(f"❌ Wildberries: ошибка — {e}")

    # Ozon
    try:
        ozon_products = search_ozon(
            query,
            mode=mode,
            slow=slow,
            use_profile=use_profile,
            profile_dir=profile_dir,
        )
        all_products.extend(ozon_products)
        print(f"📦 Ozon: найдено {len(ozon_products)}")
    except Exception as e:
        print(f"❌ Ozon: ошибка — {e}")

    return all_products


def main() -> None:
    """
    Точка входа CLI: парсит аргументы, запускает сбор данных и сохраняет CSV.
    """
    parser = build_cli()
    args = parser.parse_args()

    products = run_searches(
        args.query,
        args.mode,
        slow=args.slow,
        use_profile=args.profile,
        profile_dir=args.profile_dir,
    )

    if not products:
        print("\n⚠️ Ничего не найдено ни на одном сайте.")
        return

    export_to_csv(products, args.output)
    print(f"\n✅ Всего найдено {len(products)} товаров. Сохранено в файл {args.output}")


if __name__ == "__main__":
    main()
