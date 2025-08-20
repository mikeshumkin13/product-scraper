import pytest
pytestmark = pytest.mark.goldapple

from parser.goldapple_search import _is_good_product_url, _country_from_panel


def test_is_good_product_url():
    assert _is_good_product_url("https://goldapple.ru/190000123456-some-slug")
    assert not _is_good_product_url("https://goldapple.ru/faq")
    assert not _is_good_product_url("https://example.com/190000123456-x")


def test_country_from_panel_variants():
    txt = "Страна происхождения\nФранция\n\nПроизводитель: ..."
    assert _country_from_panel(txt) == "Франция"
    txt2 = "Изготовитель: ... ОАЭ. Адрес: ..."
    assert _country_from_panel(txt2) == "ОАЭ"
