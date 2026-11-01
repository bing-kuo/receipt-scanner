"""Thin QR decoding wrapper, plus splitting of the 77 fixed characters of the Taiwan e-invoice left QR.

Per the Ministry of Finance e-invoice QR specification, the first 77 characters are fixed-length with no delimiters:

    Offset (0-based)  Length  Field
    0                 10      Invoice number (2 letters + 8 digits)
    10                7       Issue date (ROC calendar, yyymmdd)
    17                4       Random code
    21                8       Sales amount (before tax, hex)
    29                8       Total amount (including tax, hex)
    37                8       Buyer tax ID (00000000 = consumer)
    45                8       Seller tax ID
    53                24      Encrypted verification info (AES + Base64)
    77                -       Then ":"-delimited: seller private area, item count, encoding (0 Big5 / 1 UTF-8 / 2 Base64), items...

Note: the 24-character encrypted verification info can only be verified with the seller's AES key, which we do not have,
so it is not verified and the output must never claim the invoice is "verified authentic". The right-side QR starts
with "**" and continues the item list; it is out of scope for this slice.
"""

import re
from datetime import date

import zxingcpp
from PIL import Image

from receipt.models import QRFields

_INVOICE_RE = re.compile(r"[A-Z]{2}\d{8}")
_DIGITS8_RE = re.compile(r"\d{8}")
_NO_BUYER = "00000000"


def decode_qr_texts(image: Image.Image) -> list[str]:
    """Return the text of every QR code in the image, or an empty list if none can be decoded."""
    results = zxingcpp.read_barcodes(image, formats=zxingcpp.BarcodeFormat.QRCode)
    return [r.text for r in results if r.valid]


def _roc_to_iso(s: str) -> str | None:
    if not re.fullmatch(r"\d{7}", s):
        return None
    try:
        return date(int(s[:3]) + 1911, int(s[3:5]), int(s[5:7])).isoformat()
    except ValueError:
        return None


def parse_einvoice_left(text: str) -> QRFields | None:
    """Parse the first 77 characters of the left QR. Return None on a format mismatch (not an e-invoice QR, or a decoding error)."""
    if len(text) < 77 or text.startswith("**"):
        return None
    invoice, roc, rand = text[0:10], text[10:17], text[17:21]
    sales_hex, total_hex = text[21:29], text[29:37]
    buyer, seller = text[37:45], text[45:53]

    iso = _roc_to_iso(roc)
    if not (
        _INVOICE_RE.fullmatch(invoice)
        and iso
        and _DIGITS8_RE.fullmatch(buyer)
        and _DIGITS8_RE.fullmatch(seller)
        and re.fullmatch(r"[0-9A-Za-z]{4}", rand)
    ):
        return None
    try:
        sales, total = int(sales_hex, 16), int(total_hex, 16)
    except ValueError:
        return None

    return QRFields(
        invoice_number=invoice,
        date=iso,
        random_code=rand,
        sales_amount=sales,
        total_amount=total,
        buyer_tax_id=None if buyer == _NO_BUYER else buyer,
        seller_tax_id=seller,
    )


def find_einvoice_fields(image: Image.Image) -> QRFields | None:
    """Scan all QR codes in the image and return the first one matching the e-invoice left format."""
    for text in decode_qr_texts(image):
        fields = parse_einvoice_left(text)
        if fields:
            return fields
    return None
