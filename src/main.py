from parser.books_parser import BooksParser
from utils.csv_export import export_to_csv

if __name__ == "__main__":
    url = "https://books.toscrape.com/catalogue/category/books/science_22/index.html"
    parser = BooksParser()
    products = parser.run(url)

    export_to_csv(products)

    for p in products[:3]:
        print(f"{p['name']} — {p['price']} ₽\n{p['url']}\n")

