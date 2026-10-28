"""QR 解碼的薄包裝,以及電子發票左側 QR 的 77 碼固定欄位切割。

依財政部電子發票 QR Code 規格,前 77 個字元是固定長度、無分隔符號:

    位置(0-based)  長度  欄位
    0               10    發票字軌號碼(2 英文 + 8 數字)
    10              7     開立日期(民國年 yyymmdd)
    17              4     隨機碼
    21              8     銷售額(未稅,16 進位)
    29              8     總計額(含稅,16 進位)
    37              8     買方統一編號(00000000 = 一般消費者)
    45              8     賣方統一編號
    53              24    加密驗證資訊(AES + Base64)
    77              -     之後以 ":" 分隔:營業人自用區、品項筆數、編碼參數(0 Big5 / 1 UTF-8 / 2 Base64)、品項...

注意:24 碼加密驗證資訊需要賣方的 AES 金鑰才能驗證,我們沒有,所以不驗,
輸出也不能宣稱「已驗證真偽」。右側 QR 以 "**" 開頭,是品項續行,這個切片不處理。
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
    """回傳圖片中所有 QR code 的文字。解不出來回傳空 list。"""
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
    """解析左側 QR 前 77 碼。格式不符回傳 None(不是電子發票 QR,或解碼錯誤)。"""
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
    """掃描圖片中所有 QR,回傳第一個符合電子發票左側格式的結果。"""
    for text in decode_qr_texts(image):
        fields = parse_einvoice_left(text)
        if fields:
            return fields
    return None
