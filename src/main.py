import argparse
from parser.books_parser import BooksParser
from utils.csv_export import export_to_csv


def main():
    parser = argparse.ArgumentParser(description="Парсинг товаров с сайта")
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Ссылка на страницу категории товаров",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="products.csv",
        help="Имя выходного CSV-файла (по умолчанию: products.csv)",
    )

    args = parser.parse_args()

    books_parser = BooksParser()
    try:
        products = books_parser.run(args.url)
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {e}")
        return

    export_to_csv(products, args.output)


if __name__ == "__main__":
    main()


