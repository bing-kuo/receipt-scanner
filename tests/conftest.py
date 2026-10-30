import pytest
import qrcode
from PIL import Image

# Synthetic data, not a real invoice: number AB12345678, ROC date 115-05-13, random code 1234,
# pre-tax 0x4C=76, total 0x50=80, no buyer tax ID, seller tax ID 12345678, 24 "A"s as the encrypted field.
FAKE_LEFT = "AB12345678115051312340000004C000000500000000012345678" + "A" * 24
FAKE_LEFT += ":**********:1:1:1:測試品項:1:80"


@pytest.fixture
def fake_invoice_image(tmp_path) -> Image.Image:
    return qrcode.make(FAKE_LEFT, box_size=8, border=4).convert("RGB")


@pytest.fixture
def blank_image() -> Image.Image:
    return Image.new("RGB", (400, 400), "white")
