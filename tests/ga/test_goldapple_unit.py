import pytest
pytestmark = pytest.mark.goldapple

from types import SimpleNamespace

from parser.goldapple_search import (
    _is_good_product_url,
    _jsonld_product,
    _country_from_panel,
    _rating_from_dom,
)
from utils.text_utils import clean_text, shorten_text


def test_is_good_product_url():
    assert _is_good_product_url("https://goldapple.ru/123456-my-perfume")
    assert _is_good_product_url("/123456-another-item")
    assert not _is_good_product_url("https://goldapple.ru/faq")
    assert not _is_good_product_url("https://example.com/123456-foo")


def test_jsonld_product_dict_and_list():
    html1 = (
        '<script type="application/ld+json">'
        '{"@type":"Product","name":"Test","aggregateRating":{"ratingValue":4.7}}'
        "</script>"
    )
    d1 = _jsonld_product(html1)
    assert d1.get("@type") == "Product" and d1.get("name") == "Test"

    html2 = (
        '<script type="application/ld+json">'
        '[{"@type":"BreadcrumbList"},{"@type":"Product","name":"X"}]'
        "</script>"
    )
    d2 = _jsonld_product(html2)
    assert d2.get("@type") == "Product" and d2.get("name") == "X"


def test_country_from_panel():
    t1 = "Состав\n...\nСтрана происхождения\nФранция\nИзготовитель: ..."
    assert _country_from_panel(t1) == "Франция"

    t2 = "Производство — Италия. Описание товара…"
    assert _country_from_panel(t2) == "Италия"

    t3 = "Без указания страны"
    assert _country_from_panel(t3) == ""


def test_rating_from_dom_jsonld_and_visible():
    html_jsonld = (
        '<script type="application/ld+json">'
        '{"@type":"Product","aggregateRating":{"ratingValue":"4,8"}}'
        "</script>"
    )
    driver1 = SimpleNamespace(page_source=html_jsonld)
    assert _rating_from_dom(driver1) == "4.8"

    # видимое число рядом с «оценка товара»
    html_visible = "<div>оценка товара <span>4.6</span></div>"
    driver2 = SimpleNamespace(page_source=html_visible)
    assert _rating_from_dom(driver2) == "4.6"


def test_text_utils_clean_and_shorten():
    s = "  A \n\n \n B\t\tC "
    assert clean_text(s) == "A\n\nB C"

    long = "Предложение один. Предложение два — длинное и информативное! Три?"
    cut = shorten_text(long, 25)
    assert len(cut) <= 26  # + «…»
    assert cut.endswith("…")




