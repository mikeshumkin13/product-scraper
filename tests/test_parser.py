import os
from parser.books_parser import BooksParser


def test_books_parser_parses_html_correctly():
    # Путь к фикстуре
    file_path = os.path.join(
        os.path.dirname(__file__), "data", "sample_books_page.html"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    parser = BooksParser()
    products = parser.parse(html)

    # Проверим, что хотя бы 1 товар есть
    assert len(products) > 0
    # Проверим структуру первого товара
    product = products[0]
    assert "name" in product
    assert "url" in product
    assert "price" in product
