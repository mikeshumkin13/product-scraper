import argparse
from utils.csv_export import export_to_csv
from parser.dns_search import search_dns
from parser.citilink_search import search_citilink
from parser.wildberries_search import search_wildberries
from parser.ozon_search import search_ozon


def main():
    parser = argparse.ArgumentParser(description="🛍 Product Scraper")

    parser.add_argument(
        "--mode",
        type=str,
        choices=["real", "mock"],
        default="real",
        help="🛠 Режим работы: real или mock",
    )
    parser.add_argument("--query", type=str, help="🔍 Название товара для поиска")
    parser.add_argument(
        "--output", type=str, default="results.csv", help="📁 Имя CSV файла"
    )
    args = parser.parse_args()

    if not args.query:
        print("⚠️ Укажи --query. Пример: --query 'iPhone 15'")
        return

    query = args.query
    all_products = []

    print(f"🔎 Ищем товары по запросу: {query}\n")

    # DNS
    try:
        dns_products = search_dns(query, mode=args.mode)
        all_products.extend(dns_products)
        print(f"📦 DNS: найдено {len(dns_products)}")
    except Exception as e:
        print(f"❌ DNS: ошибка — {e}")

    # Citilink
    try:
        citilink_products = search_citilink(query, mode=args.mode)
        all_products.extend(citilink_products)
        print(f"📦 Citilink: найдено {len(citilink_products)}")
    except Exception as e:
        print(f"❌ Citilink: ошибка — {e}")

    # Wildberries (mock уже работает!)
    try:
        wb_products = search_wildberries(query, mode=args.mode)
        all_products.extend(wb_products)
        print(f"📦 Wildberries: найдено {len(wb_products)}")
    except Exception as e:
        print(f"❌ Wildberries: ошибка — {e}")

    # Ozon
    try:
        ozon_products = search_ozon(query, mode=args.mode)
        all_products.extend(ozon_products)
        print(f"📦 Ozon: найдено {len(ozon_products)}")
    except Exception as e:
        print(f"❌ Ozon: ошибка — {e}")

    # Итог
    if not all_products:
        print("\n⚠️ Ничего не найдено ни на одном сайте.")
        return

    export_to_csv(all_products, args.output)
    print(
        f"\n✅ Всего найдено {len(all_products)} товаров. Сохранено в файл {args.output}"
    )


if __name__ == "__main__":
    main()
