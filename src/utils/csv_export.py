import csv
from parser.base import Product
from dataclasses import is_dataclass, asdict


def export_to_csv(data: list, filename: str) -> None:
    """
    Экспорт списка товаров в CSV.
    Поддерживает как dataclass Product, так и обычные dict.
    """
    if not data:
        print("⚠️ Нет данных для экспорта.")
        return

    # Определяем поля по первому элементу
    first_item = data[0]
    if is_dataclass(first_item):
        fieldnames = list(asdict(first_item).keys())
    elif isinstance(first_item, dict):
        fieldnames = list(first_item.keys())
    else:
        fieldnames = ["name", "price", "url"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for product in data:
            if is_dataclass(product):
                writer.writerow(asdict(product))
            elif isinstance(product, dict):
                writer.writerow(product)
            else:
                writer.writerow(
                    {field: getattr(product, field, "") for field in fieldnames}
                )


