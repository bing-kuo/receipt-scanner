from receipt.qr import decode_qr_texts, find_einvoice_fields, parse_einvoice_left
from tests.conftest import FAKE_LEFT


def test_parse_fixed_fields():
    f = parse_einvoice_left(FAKE_LEFT)
    assert f is not None
    assert f.invoice_number == "AB12345678"
    assert f.date == "2026-05-13"  # ROC year 115 + 1911
    assert f.random_code == "1234"
    assert (f.sales_amount, f.total_amount) == (76, 80)
    assert f.buyer_tax_id is None  # 00000000 = consumer
    assert f.seller_tax_id == "12345678"


def test_buyer_tax_id_present():
    text = FAKE_LEFT[:37] + "87654321" + FAKE_LEFT[45:]
    assert parse_einvoice_left(text).buyer_tax_id == "87654321"


def test_rejects_malformed():
    assert parse_einvoice_left("short") is None
    assert parse_einvoice_left("**" + FAKE_LEFT) is None  # right-side QR
    assert parse_einvoice_left(FAKE_LEFT[:10] + "1151345" + FAKE_LEFT[17:]) is None  # month 13, day 45
    assert parse_einvoice_left(FAKE_LEFT[:21] + "ZZZZZZZZ" + FAKE_LEFT[29:]) is None  # not hex


def test_decode_from_image(fake_invoice_image):
    assert decode_qr_texts(fake_invoice_image) == [FAKE_LEFT]
    assert find_einvoice_fields(fake_invoice_image).total_amount == 80


def test_no_qr(blank_image):
    assert decode_qr_texts(blank_image) == []
    assert find_einvoice_fields(blank_image) is None
