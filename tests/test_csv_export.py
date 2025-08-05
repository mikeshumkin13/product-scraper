import os
import csv
from utils.csv_export import export_to_csv


def test_export_to_csv_creates_file(tmp_path):
    # Пример данных
    products = [
        {"name": "Test Product", "url": "http://example.com", "price": "99.99 ₽"},
    ]
    # Путь до временного CSV
    file_path = tmp_path / "test.csv"

    # Экспортируем
    export_to_csv(products, file_path)

    # Проверим, что файл создан
    assert file_path.exists()

    # Проверим содержимое
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "Test Product"
