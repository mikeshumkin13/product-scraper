import pytest
pytestmark = pytest.mark.goldapple

from utils.text_utils import clean_text, shorten_text, digits


def test_clean_text():
    s = "  A \n\n \n B\t\tC "
    assert clean_text(s) == "A\n\nB C"


def test_shorten_text_sentence_boundary():
    s = "Раз. Два! Три?"
    out = shorten_text(s, 5)
    assert out.endswith("…")
    assert "Раз" in out


def test_digits():
    assert digits("7 104 ₽") == "7104"
    assert digits("12,345.00") == "1234500"

