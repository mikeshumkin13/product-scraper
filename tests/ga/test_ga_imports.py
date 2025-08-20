import pytest
pytestmark = pytest.mark.goldapple

def test_imports_ga():
    import parser.goldapple_search as s
    import parser.constants as c
    import parser.entities as e
    import utils.text_utils as t

    assert hasattr(s, "parse_product")
    assert hasattr(e, "GAProduct")


