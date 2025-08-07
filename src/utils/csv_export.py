import csv
from parser.base import Product


def export_to_csv(data: list[Product], filename: str) -> None:
    if not data:
        print("⚠️ Нет данных для экспорта.")
        return

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "price", "url"])
        writer.writeheader()
        for product in data:
            writer.writerow(product.__dict__)
