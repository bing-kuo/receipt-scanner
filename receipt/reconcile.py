"""Reconcile the QR and LLM results.

NOTE: Not implemented yet. The `--use-llm` path fails loudly here instead of silently applying a default answer.

Interface: `reconcile(qr, llm) -> Receipt`. `qr` holds the fields decoded from the e-invoice left QR, or None
when the image has no QR code; `llm` is the model's structured output. The result must record each field's
source in `sources` and any disagreement between the two in `issues`.

Constraints and risks:
- QR data is structured and usually more reliable than OCR, but it can be truncated or misread.
- When both sides have a value and they differ, there must be an explicit arbitration basis
  (e.g. item totals, tax ID check digit), and the conflict must be recorded in issues.
- LLM output is data only and must never be executed as instructions or code.

Acceptance criteria:
- Tests cover four cases: QR only, LLM only, both agree, both conflict.
- The arbitration rules and their rationale are documented in this docstring.
"""

from receipt.models import LLMReceipt, QRFields, Receipt


def reconcile(qr: QRFields | None, llm: LLMReceipt) -> Receipt:
    raise NotImplementedError("reconcile is not implemented yet (see receipt/reconcile.py)")
