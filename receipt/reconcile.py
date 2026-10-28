"""TODO(Bing): QR 與 LLM 結果不一致時以誰為準,由你決定。

介面:輸入 QR 解出的欄位(可能為 None,例如圖片沒有 QR)與 LLM 的結果,輸出合併後的 Receipt,
並在 sources 記錄每個欄位的來源、在 issues 記錄不一致。
思考方向:QR 欄位是結構化資料、錯誤率通常低於 OCR,但 QR 也可能被截斷或掃錯;
兩邊都有值卻不同時,你要靠什麼證據決定?
"""

from receipt.models import LLMReceipt, QRFields, Receipt


def reconcile(qr: QRFields | None, llm: LLMReceipt) -> Receipt:
    raise NotImplementedError("合併規則由 Bing 撰寫(見 receipt/reconcile.py)")
