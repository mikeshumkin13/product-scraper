import csv
from typing import Any, Dict, Iterable

try:
    # опционально: если Product есть, хорошо; если нет — не критично
    from parser.base import Product  # type: ignore
except Exception:
    Product = object  # fall back


def _to_row(obj: Any) -> Dict[str, Any]:
    """Приводим любой объект к dict для csv."""
    if isinstance(obj, dict):
        return dict(obj)
    # dataclass/обычный объект
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    # последний шанс — строка в name
    return {"name": str(obj)}


def _build_fieldnames(rows: Iterable[Dict[str, Any]]) -> list[str]:
    base_order = ["name", "price", "currency", "url", "image"]
    all_keys: set[str] = set()
    for r in rows:
        all_keys.update(r.keys())
    fieldnames: list[str] = [k for k in base_order if k in all_keys]
    rest = sorted(all_keys - set(fieldnames))
    fieldnames.extend(rest)
    return fieldnames


def export_to_csv(data: list[Any], filename: str) -> None:
    if not data:
        print("⚠️ Нет данных для экспорта.")
        return

    # нормализуем все элементы к словарям
    rows = [_to_row(p) for p in data]
    fieldnames = _build_fieldnames(rows)

    with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
