import argparse
import sys

from parser.books_parser import BooksParser
from utils.csv_export import export_to_csv


def main():
    parser = argparse.ArgumentParser(description="Product Scraper — парсинг товаров и экспорт в CSV.")
    parser.add_argument('--url', type=str, required=True, help='URL страницы для парсинга')
    parser.add_argument('--output', type=str, default='products.csv', help='Имя файла для сохранения результатов (по умолчанию: products.csv)')

    args = parser.parse_args()

    try:
        scraper = BooksParser()
        html = scraper.fetch_page(args.url)
        products = scraper.parse(html)
        export_to_csv(products, args.output)
        print(f"✅ Данные успешно сохранены в {args.output}")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


