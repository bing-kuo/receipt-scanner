"""Validation rules.

Interface:
- `validate(receipt, today=None) -> list[Issue]` runs on the reconciled receipt (QR-only and LLM paths).
- `llm_value_is_valid(name, value) -> bool` is used by reconcile.py to reject malformed LLM-only values
  before they reach a final field (M-1).

`Receipt.needs_review` is true whenever any issue (warning or error) exists. In particular any QR/LLM
disagreement, any LLM-only value and any rule below sends the receipt to manual review.

Issue messages are fixed text and never embed field values: values may come from the LLM or from a
forged QR and are untrusted (log injection, prompt injection).

Rules (all severity "error" unless noted):
- Amounts (integers only, never float):
  - total_amount > 0 and <= MAX_AMOUNT.
  - sales_amount <= total_amount. sales_amount == 0 is allowed (tax cannot be separated) and skips
    the tax check.
  - When sales_amount > 0, tax = total - sales must equal round(sales * 5%) within TAX_TOLERANCE.
    Zero-rated / tax-exempt invoices will be flagged; that is a known false positive.
- Tax ID (seller and buyer): 8 ASCII digits and a valid check digit. Weights 1,2,1,2,1,2,4,1; sum the
  digits of each product. Since 2023 the Ministry of Finance rule is "sum divisible by 5" (previously
  10); every old-rule ID also passes the new rule, so only the new rule is checked. When the 7th digit
  is 7 its product (28) contributes either 1 or 0, and the ID is valid if either sum passes.
- Date: ISO 8601 calendar date between MIN_DATE and today + 1 day.
- Not covered: item totals (items are not extracted yet) and the 24-character encrypted QR field,
  which needs the seller's AES key. A consistent forged QR can pass every rule; passing validation
  never means the invoice is verified authentic.
"""

import datetime as dt
import re

from receipt.models import Issue, Receipt

MAX_AMOUNT = 99_999_999  # 8 digits; larger values are not plausible for this PoC
TAX_RATE_PERCENT = 5
TAX_TOLERANCE = 1  # NTD, rounding differences
MIN_DATE = dt.date(2012, 1, 1)  # before the e-invoice QR format was in wide use

_INVOICE_NUMBER = re.compile(r"[A-Z]{2}[0-9]{8}")
_TAX_ID = re.compile(r"[0-9]{8}")
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
# Tax ID (unified business number) check weights, one per digit, left to right.
# Each digit is multiplied by its weight, the digits of each product are summed
# (e.g. 18 -> 1 + 8), and the total must be divisible by 5. Before the 2023
# revision the divisor was 10; every number valid under the old rule is still
# valid under the new one, so checking divisibility by 5 accepts both.
# Special case: when the 7th digit is 7, its product is 28 -> 10, which may
# count as 1 or 0, so the ID is valid if either total passes.
# Source: Ministry of Finance, Fiscal Information Agency, "Revised check digit
# logic for the business unified number":
# https://www.fia.gov.tw/singlehtml/3?cntId=c4d9cff38c8642ef8872774ee9987283
_WEIGHTS = (1, 2, 1, 2, 1, 2, 4, 1)


def _parse_date(value: str) -> dt.date | None:
    # fullmatch with explicit [0-9]: rejects full-width digits, ROC dates and trailing newlines
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def _is_amount(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 < value <= MAX_AMOUNT


def llm_value_is_valid(name: str, value) -> bool:
    """Format check for an LLM value. Unknown field names are rejected."""
    if name == "invoice_number":
        return isinstance(value, str) and _INVOICE_NUMBER.fullmatch(value) is not None
    if name == "seller_tax_id":
        return isinstance(value, str) and _TAX_ID.fullmatch(value) is not None
    if name == "date":
        return _parse_date(value) is not None
    if name == "total_amount":
        return _is_amount(value)
    return False


def tax_id_is_valid(tax_id: str) -> bool:
    if not isinstance(tax_id, str) or not _TAX_ID.fullmatch(tax_id):
        return False
    digits = [int(c) for c in tax_id]
    total = 0
    for i, (d, w) in enumerate(zip(digits, _WEIGHTS, strict=True)):
        if i == 6 and d == 7:
            continue  # 28 -> 2+8=10 -> counts as 1 or 0, handled below
        p = d * w
        total += p // 10 + p % 10
    if digits[6] == 7:
        return total % 5 == 0 or (total + 1) % 5 == 0
    return total % 5 == 0


def _error(code: str, message: str) -> Issue:
    return Issue(code=code, message=message, severity="error")


def validate(receipt: Receipt, today: dt.date | None = None) -> list[Issue]:
    today = today or dt.date.today()
    issues: list[Issue] = []

    total, sales = receipt.total_amount, receipt.sales_amount
    if total is not None:
        if not _is_amount(total):
            issues.append(_error("total_amount_out_of_range", "total_amount is out of range"))
        elif sales is not None:
            if not isinstance(sales, int) or isinstance(sales, bool) or sales < 0 or sales > total:
                issues.append(
                    _error("sales_amount_invalid", "sales_amount is negative or exceeds total_amount")
                )
            elif sales > 0:
                expected = (sales * TAX_RATE_PERCENT + 50) // 100  # round half up, integer only
                if abs((total - sales) - expected) > TAX_TOLERANCE:
                    issues.append(
                        _error("tax_amount_mismatch", "tax amount does not match 5% of sales_amount")
                    )

    for name in ("seller_tax_id", "buyer_tax_id"):
        value = getattr(receipt, name)
        if value is not None and not tax_id_is_valid(value):
            issues.append(_error(f"{name}_checksum", f"{name} fails the check digit rule"))

    if receipt.date is not None:
        d = _parse_date(receipt.date)
        if d is None or not (MIN_DATE <= d <= today + dt.timedelta(days=1)):
            issues.append(_error("date_out_of_range", "date is invalid or outside the plausible range"))

    return issues
