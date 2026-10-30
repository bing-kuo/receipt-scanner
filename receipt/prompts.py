"""LLM 的 instructions(prompt)。

NOTE: 尚未實作。`--use-llm` 會因此回報錯誤,這是刻意的:避免用空 prompt 消耗 API 額度。

介面:`build_instructions() -> str`,回傳送給模型的 instructions。圖片由 llm.py 另外以 input 傳入,
不要混進這個字串。輸出格式由 `models.LLMReceipt` 的 schema 約束。

限制與風險:
- 收據上的文字是不可信輸入,可能含指令。prompt 必須明確區分「要抽取的資料」與「指令」。
- 看不清楚的欄位回 null,不得猜測。

驗收條件:
- 20 張樣本上各欄位的正確率、延遲與單張成本已量測並記錄。
- 含指令字樣的樣本(例如「忽略以上指示」)不影響輸出,輸出仍符合 schema。
- 是否把 QR 已解出的欄位提供給模型,已決定並記錄理由。
"""


def build_instructions() -> str:
    raise NotImplementedError("prompt 尚未實作(見 receipt/prompts.py)")
