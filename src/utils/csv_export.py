import csv
from typing import List, Dict


def export_to_csv(data: List[Dict], filename: str = "products.csv") -> None:
    if not data:
        print("Нет данных для экспорта.")
        return

    fieldnames = data[0].keys()
    with open(str(filename), mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"Данные успешно сохранены в {filename}")


