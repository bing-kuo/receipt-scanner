import pytest

from receipt.prompts import build_instructions


def test_build_instructions_format():
    text = build_instructions()
    assert isinstance(text, str)
    assert text.strip()
    assert "\t" not in text
    assert not text.startswith(" ")


@pytest.mark.parametrize(
    "field_name", ["date", "invoice_number", "seller_tax_id", "seller_name", "total_amount", "items"]
)
def test_build_instructions_field(field_name):
    text = build_instructions()
    assert field_name in text
