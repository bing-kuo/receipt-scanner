"""Reconcile the QR and LLM results.

Interface: `reconcile(qr, llm) -> Receipt`. `qr` holds the fields decoded from the e-invoice left QR, or None
when the image has no QR code; `llm` is the model's structured output. The result must record each field's
source in `sources` and any disagreement between the two in `issues`.

Arbitration rules:
- Only QR: use the QR value.
- Only LLM: use the LLM value and record a warning, because there is no second source to cross-check.
- Both agree: use the QR value.
- Both differ: use the QR value and record an error. QR is structured data and more reliable than
  LLM reading, but a truncated or misread QR is not caught here; validate.py is the real defense.
- Neither: the field stays empty and an error is recorded.

Constraints and risks:
- QR data is structured and usually more reliable than OCR, but it can be truncated or misread.
- When both sides have a value and they differ, an explicit arbitration basis is needed
  (e.g. tax ID check digit, amount consistency). For now the QR value is used by default and the conflict
  is recorded in issues; the validation rules themselves live in `validate.py`.
- LLM output is data only and must never be executed as instructions or code.
- The LLM-only path is the riskiest: its values are unverified and a prompt-injected image could
  influence them. It is flagged as a warning so that the receipt goes to manual review.

Acceptance criteria:
- Tests cover five cases: QR only, LLM only, both agree, both conflict, neither.
"""

from receipt.models import Issue, LLMReceipt, QRFields, Receipt, Source


def pick(name, qr_val, llm_val) -> tuple[str | int | None, Source | None, Issue | None]:
    """Return (value, source, issue) for a single field."""
    if qr_val is None and llm_val is None:
        return None, None, Issue(code=f"{name}_missing", message=f"{name} is not found", severity="error")
    if llm_val is None:  # QR only
        return qr_val, "qr", None
    if qr_val is None:  # LLM only: no second source to cross-check
        return (
            llm_val,
            "llm",
            Issue(code=f"{name}_qr_missing", message=f"{name} is only from LLM", severity="warning"),
        )
    if qr_val == llm_val:  # both agree
        return qr_val, "qr", None

    # both present but different
    issue = Issue(
        code=f"{name}_conflict", message=f"{name} differs: qr={qr_val}, llm={llm_val}", severity="error"
    )
    value, source = qr_val, "qr"
    return value, source, issue


def reconcile(qr: QRFields | None, llm: LLMReceipt) -> Receipt:
    r = Receipt()

    for name in ["invoice_number", "date", "seller_tax_id", "total_amount"]:
        qr_val = None if qr is None else getattr(qr, name)
        llm_val = getattr(llm, name)
        value, source, issue = pick(name, qr_val, llm_val)
        setattr(r, name, value)
        if source is not None:
            r.sources[name] = source
        if issue is not None:
            r.issues.append(issue)

    # Only QR
    r.buyer_tax_id = None if qr is None else qr.buyer_tax_id
    if qr is not None and qr.buyer_tax_id is not None:
        r.sources["buyer_tax_id"] = "qr"

    r.sales_amount = None if qr is None else qr.sales_amount
    if qr is not None and qr.sales_amount is not None:
        r.sources["sales_amount"] = "qr"

    return r
