"""驗證規則。

NOTE: 尚未實作,目前一律回傳空 list(代表沒發現問題,不代表資料正確)。

介面:`validate(receipt) -> list[Issue]`。每個 Issue 有 code、message 與 severity(warning / error)。
`Receipt.needs_review` 目前以「有任何 issue 即需人工」為最保守預設,退回人工的條件在此一併定義。

範圍:
- 金額:未稅與含稅金額的關係、品項加總與總額是否相符。
- 統編:格式與檢查碼(財政部規則曾改版,實作時需確認當前版本)。
- 日期:是否落在合理範圍。
- 不驗證 QR 的 24 碼加密欄位(需要賣方 AES 金鑰),輸出也不得宣稱「已驗證真偽」。

驗收條件:
- 每條規則至少有一個通過案例與一個觸發案例的測試。
- 每條規則都註明觸發時的 severity 與理由。
- 在 20 張樣本上,誤報(正確資料被標為有問題)與漏報的情況已記錄。
"""

from receipt.models import Issue, Receipt


def validate(receipt: Receipt) -> list[Issue]:
    return []  # NOTE: 尚未實作
