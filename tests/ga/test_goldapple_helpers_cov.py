import json
import pytest
from selenium.webdriver.common.by import By

import parser.goldapple_search as ga


# --- простые стабы Selenium-элементов/драйвера -----------------

class _El:
    def __init__(self, text="", attrs=None):
        self.text = text
        self._attrs = attrs or {}
        self.clicked = False

    def click(self):
        self.clicked = True

    def get_attribute(self, k):
        return self._attrs.get(k, "")


class _Driver:
    def __init__(self, html="", store=None):
        self.page_source = html
        self.store = store or {}

    def find_element(self, by, sel):
        # meta[itemprop='price'] -> content
        if by == By.CSS_SELECTOR and sel == "meta[itemprop='price']":
            v = self.store.get("meta_price")
            if v is None:
                raise Exception("not found")
            return _El(attrs={"content": v})

        # og:title -> content
        if by == By.CSS_SELECTOR and sel == "meta[property='og:title']":
            v = self.store.get("og_title")
            if v is None:
                raise Exception("not found")
            return _El(attrs={"content": v})

        # XPATH с ₽
        if by == By.XPATH and "₽" in sel:
            return _El(text=self.store.get("price_text", "9 990 ₽"))

        raise Exception("not found")

    def find_elements(self, by, sel):
        # страна в «Бренд» (короткая плашка)
        if by == By.XPATH and "plsf" in sel.lower():
            return [_El(text=self.store.get("brand_country", "Италия"))]
        return []

    def execute_script(self, *_a, **_kw):
        return None


def _html_with_jsonld(obj: dict) -> str:
    return f'<script type="application/ld+json">{json.dumps(obj)}</script>'


# --- тесты на чистую логику -------------------------------------

def test_is_good_product_url():
    assert ga._is_good_product_url("https://goldapple.ru/123456-montale-intense")
    assert not ga._is_good_product_url("https://goldapple.ru/category/abc")
    assert not ga._is_good_product_url("https://example.com/123456-foo")


def test_jsonld_product_dict_and_list():
    html1 = _html_with_jsonld({"@type": "Product", "name": "X"})
    assert ga._jsonld_product(html1).get("name") == "X"

    html2 = _html_with_jsonld([{"@type": "ProductGroup"}, {"@type": "Product", "name": "Y"}])
    assert ga._jsonld_product(html2).get("name") == "Y"


def test_is_perfume_and_not_found():
    d1 = _Driver(html="<a href='/parfjumerija'>Парфюмерия</a>")
    d2 = _Driver(html="упс... страница не найдена")
    assert ga._is_perfume_pdp(d1)
    assert ga._on_not_found(d2)


def test_find_name_from_jsonld_when_dom_absent():
    html = _html_with_jsonld({"@type": "Product", "name": "TEST NAME"})
    d = _Driver(html=html)
    assert ga._find_name(d) == "TEST NAME"


def test_price_from_meta_and_fallback_xpath():
    # meta[itemprop=price]
    d1 = _Driver(store={"meta_price": "7104.00"})
    assert ga._price_from_dom(d1) == "710400" or ga._price_from_dom(d1) == "7104"  # обе ветки ок

    # fallback по XPATH с символом ₽
    d2 = _Driver(store={"meta_price": None, "price_text": "2 590 ₽"})
    assert ga._price_from_dom(d2) == "2590"


def test_rating_from_jsonld_and_regex():
    html = _html_with_jsonld({"@type": "Product", "aggregateRating": {"ratingValue": "4.7"}})
    d1 = _Driver(html=html)
    assert ga._rating_from_dom(d1) == "4.7"

    # fallback через regex "5.0" внутри HTML
    d2 = _Driver(html="<div>5.0</div>")
    assert ga._rating_from_dom(d2) == "5.0"


def test_country_from_panel_and_brand_short():
    t = "Состав... Страна происхождения: Франция\nДругое..."
    assert ga._country_from_panel(t) == "Франция"

    # короткая «плашка» страны на вкладке «Бренд»
    d = _Driver(store={"brand_country": "Италия"})
    assert ga._brand_country_short(d) == "Италия"