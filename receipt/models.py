"""Data models. The fields are a starting point and can be added or removed as needed."""

from typing import Literal

from pydantic import BaseModel, Field, computed_field

Source = Literal["qr", "llm"]


class QRFields(BaseModel):
    """Fixed fields from the first 77 characters of the e-invoice left QR (see the table in qr.py)."""

    invoice_number: str
    date: str  # ISO 8601, converted from the ROC (Minguo) calendar year
    random_code: str
    sales_amount: int  # Sales amount before tax
    total_amount: int  # Total amount including tax
    buyer_tax_id: str | None  # None for a consumer (00000000)
    seller_tax_id: str


class Item(BaseModel):
    name: str
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class LLMReceipt(BaseModel):
    """Schema for structured LLM output. Every field may be None: return None when unreadable, never guess."""

    invoice_number: str | None = None
    date: str | None = None  # ISO 8601
    seller_tax_id: str | None = None
    seller_name: str | None = None
    total_amount: int | None = None
    items: list[Item] = Field(default_factory=list)


class Issue(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "error"] = "warning"


class Receipt(BaseModel):
    """Final output. `sources` records whether each field came from the QR code or the LLM.

    `source="qr"` only means the value was read from the QR text; it does not mean the value is verified.
    A warning, including when both amount sources are qr, does not mean the invoice is authentic or correct.
    Any issue (warning or error) keeps `needs_review` true.
    """

    invoice_number: str | None = None
    date: str | None = None
    seller_tax_id: str | None = None
    buyer_tax_id: str | None = None
    seller_name: str | None = None
    sales_amount: int | None = None
    total_amount: int | None = None
    items: list[Item] = Field(default_factory=list)
    sources: dict[str, Source] = Field(default_factory=dict)
    issues: list[Issue] = Field(default_factory=list)

    @computed_field  # serialized, so downstream consumers cannot miss the flag
    @property
    def needs_review(self) -> bool:
        # Any issue (warning or error) requires manual review; see validate.py for the rules.
        return bool(self.issues)
