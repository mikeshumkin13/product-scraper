import builtins
import json
import types
from pathlib import Path
import pytest

from parser.wildberries_search import search_wildberries
from parser.dns_search import search_dns
import utils.selenium_driver as sd


# Эмулируем падение Selenium-драйвера, чтобы парсер ушёл в mock
class Boom(Exception):
    pass


@pytest.fixture(autouse=True)
def fast_sleep(monkeypatch):
    # чтобы тесты шли быстро, даже если парсер вызывает human_sleep
    monkeypatch.setattr("time.sleep", lambda *_args, **_kw: None, raising=False)


def test_wb_real_fallback_to_mock(monkeypatch):
    monkeypatch.setattr(
        sd, "get_selenium_driver", lambda **kw: (_ for _ in ()).throw(Boom("no driver"))
    )
    items = search_wildberries("пылесос", mode="real")
    assert isinstance(items, list) and len(items) > 0  # из mock
    # минимальные инварианты
    first = items[0]
    name = first.get("name") if isinstance(first, dict) else getattr(first, "name", "")
    url = first.get("url") if isinstance(first, dict) else getattr(first, "url", "")
    assert name and url


def test_dns_real_fallback_to_mock(monkeypatch):
    monkeypatch.setattr(
        sd, "get_selenium_driver", lambda **kw: (_ for _ in ()).throw(Boom("no driver"))
    )
    items = search_dns("пылесос", mode="real")
    assert isinstance(items, list) and len(items) > 0  # из mock
    first = items[0]
    name = first.get("name") if isinstance(first, dict) else getattr(first, "name", "")
    url = first.get("url") if isinstance(first, dict) else getattr(first, "url", "")
    assert name and url
