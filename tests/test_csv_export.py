import csv
import tempfile
from typing import List, Dict

from utils.csv_export import export_to_csv
from parser.dns_search import search_dns
from parser.citilink_search import search_citilink
from parser.wildberries_search import search_wildberries
from parser.ozon_search import search_ozon

# Целевая схема CSV по договорённости проекта
SCHEMA = ["name", "price", "currency", "url", "image"]

def _as_dict(item):
    if isinstance(item, dict):
        return item
    # dataclass / объект с атрибутами
    out = {}
    for k in SCHEMA:
        if hasattr(item, k):
            out[k] = getattr(item, k)
    # гарантируем наличие ключей
    for k in SCHEMA:
        out.setdefault(k, "")
    return out

def test_export_csv_mock_end_to_end():
    # собираем из всех четырёх парсеров (mock), как делает main.py
    items: List[Dict] = []
    for fn in (search_dns, search_citilink, search_wildberries, search_ozon):
        items.extend(fn("чайник", mode="mock"))

    # нормализуем к диктам (на случай dataclass Product)
    rows = [_as_dict(x) for x in items]
    assert len(rows) > 0

    with tempfile.NamedTemporaryFile("w+b", suffix=".csv", delete=True) as tmp:
        export_to_csv(rows, tmp.name)
        tmp.seek(0)
        content = tmp.read().decode("utf-8")
        assert content.strip() != ""

        # проверим через csv.reader заголовок и пару строк
        tmp.seek(0)
        r = csv.reader(tmp.read().decode("utf-8").splitlines())
        header = next(r)
        # допускаем, что экспорт может выставлять поля в нужном порядке
        assert header == SCHEMA
        first = next(r, None)
        assert first is not None
        assert first[0] != ""   # name
        assert first[3].startswith("http") or first[3] == ""  # url может быть пуст



