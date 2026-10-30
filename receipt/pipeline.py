"""主流程:QR 優先,LLM 只在明確要求時補欄位,最後執行 validate。"""

import logging

from PIL import Image

from receipt.imageio import to_data_url
from receipt.llm import Extractor
from receipt.models import QRFields, Receipt
from receipt.qr import find_einvoice_fields
from receipt.reconcile import reconcile
from receipt.validate import validate

log = logging.getLogger(__name__)


class NoQRFound(RuntimeError):
    pass


def _from_qr(qr: QRFields) -> Receipt:
    data = qr.model_dump(exclude={"random_code"})
    return Receipt(**data, sources={k: "qr" for k, v in data.items() if v is not None})


def extract_receipt(image: Image.Image, extractor: Extractor | None = None) -> Receipt:
    """extractor 為 None 時只用 QR(零成本)。給了 extractor 才會呼叫 LLM。"""
    qr = find_einvoice_fields(image)
    log.info("qr_found=%s use_llm=%s", qr is not None, extractor is not None)

    if extractor is None:
        if qr is None:
            raise NoQRFound("找不到電子發票 QR code;可加 --use-llm 讓 LLM 讀取(會產生 API 費用)")
        receipt = _from_qr(qr)
    else:
        llm = extractor.extract(to_data_url(image))
        receipt = reconcile(qr, llm)  # 尚未實作,見 reconcile.py

    receipt.issues.extend(validate(receipt))
    return receipt
