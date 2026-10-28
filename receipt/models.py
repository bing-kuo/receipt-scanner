"""資料結構。欄位是起手式,要抽哪些欄位由 Bing 決定,可以自由增減。"""

from typing import Literal

from pydantic import BaseModel, Field

Source = Literal["qr", "llm"]


class QRFields(BaseModel):
    """電子發票左側 QR 前 77 碼的固定欄位(見 qr.py 的對照表)。"""

    invoice_number: str
    date: str  # ISO 8601,已由民國年轉西元
    random_code: str
    sales_amount: int  # 未稅銷售額
    total_amount: int  # 含稅總額
    buyer_tax_id: str | None  # 一般消費者(00000000)為 None
    seller_tax_id: str


class Item(BaseModel):
    name: str
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class LLMReceipt(BaseModel):
    """LLM 結構化輸出的 schema。所有欄位都可為 None:看不清楚就回 None,不要猜。"""

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
    """最終輸出。sources 記錄每個欄位是從 QR 還是 LLM 來的。"""

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

    @property
    def needs_review(self) -> bool:
        # TODO(Bing): 「什麼情況退回人工」是你的判斷,這裡只是最保守的預設。
        return bool(self.issues)
