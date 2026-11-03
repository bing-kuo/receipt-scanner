from receipt.models import LLMReceipt
from receipt.qr import parse_einvoice_left
from receipt.reconcile import reconcile
from tests.conftest import FAKE_LEFT


def test_reconcile_qr_only():
    qr = parse_einvoice_left(FAKE_LEFT)
    llm = LLMReceipt()
    r = reconcile(qr, llm)

    assert r.invoice_number == qr.invoice_number
    assert r.date == qr.date
    assert r.sources["invoice_number"] == "qr"
    assert r.sources["date"] == "qr"
    assert r.sources["seller_tax_id"] == "qr"
    assert r.sources["total_amount"] == "qr"
    assert r.issues == []


def test_reconcile_llm_only():
    llm = LLMReceipt(
        invoice_number="AB12345678", date="2026-12-25", seller_tax_id="12345678", total_amount=666
    )
    r = reconcile(None, llm)
    issue_code = [i.code for i in r.issues]

    assert r.invoice_number == llm.invoice_number
    assert r.sources["invoice_number"] == "llm"
    assert "invoice_number_qr_missing" in issue_code
    assert "date_qr_missing" in issue_code
    assert "seller_tax_id_qr_missing" in issue_code
    assert "total_amount_qr_missing" in issue_code


def test_reconcile_same_value():
    qr = parse_einvoice_left(FAKE_LEFT)
    llm = LLMReceipt(invoice_number="AB12345678")
    r = reconcile(qr, llm)

    assert r.invoice_number == llm.invoice_number
    assert r.date == qr.date
    assert r.sources["invoice_number"] == "qr"
    assert r.issues == []


def test_reconcile_conflict():
    qr = parse_einvoice_left(FAKE_LEFT)
    llm = LLMReceipt(invoice_number="ZZ00000000")
    r = reconcile(qr, llm)
    issue_code = [i.code for i in r.issues]

    assert r.invoice_number == qr.invoice_number
    assert r.invoice_number != llm.invoice_number
    assert r.date == qr.date
    assert r.sources["invoice_number"] == "qr"
    assert "invoice_number_conflict" in issue_code


def test_reconcile_both_empty():
    r = reconcile(None, LLMReceipt())
    issue_code = [i.code for i in r.issues]

    assert "invoice_number_missing" in issue_code
    assert "date_missing" in issue_code
    assert "seller_tax_id_missing" in issue_code
    assert "total_amount_missing" in issue_code
