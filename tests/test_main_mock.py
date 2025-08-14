from typing import List

import importlib
import types

import main as app
from parser.base import Product


def test_run_searches_mock_returns_products(monkeypatch):
    # подменим build_cli, чтобы не мешал при импортировании в других местах
    importlib.reload(app)

    # Запускаем прямую функцию, минуя CLI
    products: List[Product] = app.run_searches(
        query="чайник",
        mode="mock",
        slow=False,
        use_profile=False,
        profile_dir=None,
    )
    assert isinstance(products, list)
    assert len(products) > 0
    # Проверим пару инвариантов на первом элементе
    p = products[0]
    name = p.name if hasattr(p, "name") else p.get("name")
    url = p.url if hasattr(p, "url") else p.get("url")
    assert name and isinstance(name, str)
    assert isinstance(url, str)
