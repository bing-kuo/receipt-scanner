"""Validation rules.

NOTE: Not implemented yet; it currently always returns an empty list (meaning "no problems found",
not "the data is correct").

Interface: `validate(receipt) -> list[Issue]`. Each Issue has a code, a message and a severity (warning / error).
`Receipt.needs_review` currently uses the most conservative default (any issue requires manual review);
the criteria for sending a receipt to manual review should be defined here as well.

Scope:
- Amounts: relationship between pre-tax and total amounts; whether item totals match the total.
- Tax ID: format and check digit (the Ministry of Finance rules have changed before; confirm the current version).
- Date: whether it falls in a plausible range.
- The 24-character encrypted QR field is not verified (it needs the seller's AES key), and the output must
  never claim the invoice is "verified authentic".

Acceptance criteria:
- Every rule has at least one passing case and one triggering case in tests.
- Every rule documents its severity and rationale.
- False positives (valid data flagged) and false negatives are recorded on 20 samples.
"""

from receipt.models import Issue, Receipt


def validate(receipt: Receipt) -> list[Issue]:
    return []  # NOTE: not implemented yet
