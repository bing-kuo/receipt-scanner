"""合併 QR 與 LLM 的結果。

NOTE: 尚未實作。`--use-llm` 路徑會在這裡明確失敗,而不是悄悄套用預設答案。

介面:`reconcile(qr, llm) -> Receipt`。`qr` 為電子發票左側 QR 解出的欄位,圖片沒有 QR 時為 None;
`llm` 為模型的結構化輸出。輸出需在 `sources` 記錄每個欄位的來源,在 `issues` 記錄兩邊不一致之處。

限制與風險:
- QR 是結構化資料,通常比 OCR 可靠,但也可能被截斷或掃錯。
- 兩邊都有值且不同時,需要有明確的仲裁依據(例如金額加總、統編檢查碼),並記錄在 issues。
- LLM 輸出只當資料,不得作為指令或程式碼執行。

驗收條件:
- 涵蓋「只有 QR」「只有 LLM」「兩者一致」「兩者衝突」四種情況的測試。
- 衝突時的仲裁規則與理由寫在本檔 docstring。
"""

from receipt.models import LLMReceipt, QRFields, Receipt


def reconcile(qr: QRFields | None, llm: LLMReceipt) -> Receipt:
    raise NotImplementedError("合併規則尚未實作(見 receipt/reconcile.py)")
