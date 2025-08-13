import types
from typing import List, Dict

from parser.dns_search import search_dns
from parser.citilink_search import search_citilink
from parser.wildberries_search import search_wildberries
from parser.ozon_search import search_ozon

# Базовые инварианты результатов
REQUIRED_KEYS = {"name", "url"}  # остальное может быть пустым/отсутствовать до нормализации CSV

def _assert_items(items: List[Dict], max_len: int = 10):
    assert isinstance(items, list)
    assert 0 < len(items) <= max_len
    for it in items:
        assert isinstance(it, (dict, types.SimpleNamespace)) or hasattr(it, "__dict__")
        name = getattr(it, "name", None) if not isinstance(it, dict) else it.get("name")
        url = getattr(it, "url", None) if not isinstance(it, dict) else it.get("url")
        assert name is not None and str(name).strip() != ""
        assert url is not None and str(url).strip() != ""

def _assert_items_allow_empty(items: List[Dict], max_len: int = 10):
    # Версия проверки для кейсов, где mock-файл по запросу может дать пусто
    assert isinstance(items, list)
    assert len(items) <= max_len
    for it in items:
        assert isinstance(it, (dict, types.SimpleNamespace)) or hasattr(it, "__dict__")
        name = getattr(it, "name", None) if not isinstance(it, dict) else it.get("name")
        url = getattr(it, "url", None) if not isinstance(it, dict) else it.get("url")
        assert name is not None and str(name).strip() != ""
        assert url is not None and str(url).strip() != ""

def test_dns_mock():
    items = search_dns("чайник", mode="mock")
    # DNS mock может не содержать "чайник" — важно, что функция не падает и вернула список
    _assert_items_allow_empty(items)

def test_citilink_mock():
    items = search_citilink("чайник", mode="mock")
    _assert_items(items)

def test_wildberries_mock():
    items = search_wildberries("чайник", mode="mock")
    _assert_items(items)

def test_ozon_mock():
    items = search_ozon("чайник", mode="mock")
    _assert_items(items)

