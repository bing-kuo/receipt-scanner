"""TODO(Bing): 驗證規則由你寫。回傳 Issue list,空 list 代表沒發現問題。

可以思考的方向(不是答案):
- 金額:sales_amount 與 total_amount 的關係、品項加總對不對得上總額。
- 統編:格式與檢查碼(查財政部規則,注意規則曾經改版)。
- 日期:是否在合理範圍(未來日期?太久以前?)。
- 每條規則被觸發時,是 warning 還是 error?
"""

from receipt.models import Issue, Receipt


def validate(receipt: Receipt) -> list[Issue]:
    return []  # TODO(Bing)
