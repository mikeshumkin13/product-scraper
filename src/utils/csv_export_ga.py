from __future__ import annotations
import csv
from typing import Iterable


def export_to_csv_goldapple(rows: Iterable[dict], output_path: str) -> None:
    """
    Пишет CSV в UTF-8-BOM под Excel.
    Ожидаемые поля: url,name,price,rating,description,instructions,country
    """
    headers = [
        "url",
        "name",
        "price",
        "rating",
        "description",
        "instructions",
        "country",
    ]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            # безопасно подставляем пустые для отсутствующих ключей
            w.writerow(
                {
                    h: (r.get(h, "") if isinstance(r, dict) else getattr(r, h, ""))
                    for h in headers
                }
            )
