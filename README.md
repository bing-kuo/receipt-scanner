# acornsight-poc-receipt

台灣電子發票辨識 PoC(Issue #10 第一個切片):QR decode 先解固定欄位,LLM 只補 QR 沒有的欄位,最後用規則交叉驗證。圖片進、JSON 出。

## 快速開始

需要 Python 3.13(`.python-version`)。

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q

# 只用 QR(不花錢,不需要 key)
python -m receipt extract path/to/receipt.jpg

# 啟用 LLM(會花錢;先看下面「預算」)
cp .env.example .env   # 填入 OPENAI_API_KEY 與 RECEIPT_MODEL
python -m receipt extract path/to/receipt.jpg --use-llm
```

## 結構與分工

| 檔案 | 內容 | 誰寫 |
| --- | --- | --- |
| `receipt/qr.py` | QR 解碼薄包裝、77 碼欄位切割(附規格對照) | 骨架 |
| `receipt/llm.py` | `Extractor` 介面、OpenAI 實作、重試、timeout、呼叫上限 | 骨架 |
| `receipt/imageio.py`, `config.py`, `cli.py`, `pipeline.py` | 載入圖片、讀設定、CLI、主流程 | 骨架 |
| `receipt/prompts.py` | LLM prompt | **Bing**(stub) |
| `receipt/validate.py` | 金額、統編、日期等驗證規則,低信心判斷 | **Bing**(stub) |
| `receipt/reconcile.py` | QR 與 LLM 不一致時以誰為準 | **Bing**(stub) |

三個 stub 沒實作前,只用 QR 的路徑可以跑;加 `--use-llm` 會明確失敗(`NotImplementedError`),不會悄悄給預設答案。

## 預算(上限 US$5)

- 預設不呼叫 LLM。QR 能解的欄位不送 LLM,只在 `--use-llm` 時補其他欄位。
- 單次執行最多 `RECEIPT_MAX_LLM_CALLS` 次呼叫(含重試,預設 5)。這只是防呆;**真正的上限要在 OpenAI 後台為專用 key 設定**。
- 先用小模型,模型名稱由 `RECEIPT_MODEL` 指定,沒有預設值,避免默默用到貴的模型。
- 送出前圖片會縮到長邊 1600px 並重新編碼(同時去掉 EXIF)。

## 資安規則

- API key 只放本機 `.env`(已 ignore),不進 git、Issue、聊天。`.env.example` 只有空值。
- 啟用 pre-commit:`pip install pre-commit && pre-commit install`,commit 時會跑 gitleaks。
- 樣本圖片與正確答案檔放 `samples/`(已 ignore),不 commit;說明見 `samples/README.md`。
- 輸出只寫 stdout,不自動寫檔;若要存檔,存到 repo 外或 `out/`(已 ignore)。
- log 只記次數與錯誤類型,不記 header、圖片、LLM 原始回應。
- QR 的 24 碼加密驗證資訊需賣方 AES 金鑰,**不驗證**,輸出也不宣稱「已驗證真偽」。
- 送第三方 LLM 前,供應商的資料保留與訓練政策要先查證並記在 Issue #10。

## TODO(之後的切片)

- QR 77 碼之後的品項明細解析(編碼參數 0 Big5 / 1 UTF-8 / 2 Base64)與右側 `**` QR。
- 只送裁切過的非 QR 區域給 LLM(資料最小化)。
- 20 張樣本的 benchmark:欄位正確率、延遲、成本。
