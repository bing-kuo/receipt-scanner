import pytest
import qrcode
from PIL import Image

# 合成資料,非真實發票:字軌 AB12345678、民國 115 年 5 月 13 日、隨機碼 1234、
# 未稅 0x4C=76、含稅 0x50=80、買方無統編、賣方統編 12345678、加密欄位 24 個 A。
FAKE_LEFT = "AB12345678115051312340000004C000000500000000012345678" + "A" * 24
FAKE_LEFT += ":**********:1:1:1:測試品項:1:80"


@pytest.fixture
def fake_invoice_image(tmp_path) -> Image.Image:
    return qrcode.make(FAKE_LEFT, box_size=8, border=4).convert("RGB")


@pytest.fixture
def blank_image() -> Image.Image:
    return Image.new("RGB", (400, 400), "white")
