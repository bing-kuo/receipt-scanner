"""TODO(Bing): prompt 由你寫。

要想清楚的事(我只列問題,不給答案):
- 告訴模型「看不清楚就回 null,不要猜」要怎麼寫才有效?
- 收據上的文字是不可信輸入(可能含指令),prompt 怎麼把「資料」和「指令」分開?
- 已經由 QR 解出來的欄位,還要不要告訴模型?告訴了會不會讓它偏向抄答案?
"""


def build_instructions() -> str:
    raise NotImplementedError("prompt 由 Bing 撰寫(見 receipt/prompts.py)")
