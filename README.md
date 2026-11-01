# acornsight-poc-receipt

台灣電子發票辨識 PoC(第一個切片):QR decode 先解固定欄位,LLM 只補 QR 沒有的欄位,最後用規則交叉驗證。圖片進、JSON 出。

## 快速開始

需要 Python 3.13(`.python-version`)。

```bash
uv venv && source .venv/bin/activate   # 需先 brew install uv;Python 版本依 .python-version
uv pip install --require-hashes -r requirements-dev.txt
python -m pytest -q
uv pip install pre-commit && pre-commit install   # 只防誤 commit,不防 --no-verify

# 只用 QR(不花錢,不需要 key)
python -m receipt extract path/to/receipt.jpg

# 啟用 LLM(會花錢;先看下面「預算」)
cp .env.example .env   # 填入 OPENAI_API_KEY 與 RECEIPT_MODEL
python -m receipt extract path/to/receipt.jpg --use-llm
```

## 結構與狀態

| 檔案 | 內容 | 狀態 |
| --- | --- | --- |
| `receipt/qr.py` | QR 解碼薄包裝、77 碼欄位切割(附規格對照) | 完成 |
| `receipt/llm.py` | `Extractor` 介面、OpenAI 實作、重試、timeout、呼叫上限 | 完成 |
| `receipt/imageio.py`, `config.py`, `cli.py`, `pipeline.py` | 載入圖片、讀設定、CLI、主流程 | 完成 |
| `receipt/prompts.py` | LLM prompt | 待實作 |
| `receipt/validate.py` | 金額、統編、日期等驗證規則,低信心判斷 | 待實作 |
| `receipt/reconcile.py` | QR 與 LLM 不一致時的仲裁 | 待實作 |

三個待實作的檔案,範圍、限制與驗收條件寫在各檔 docstring。沒實作前,只用 QR 的路徑可以跑;加 `--use-llm` 會明確失敗(`NotImplementedError`),不會悄悄給預設答案。

## 開發

- 環境與測試:見上方「快速開始」。commit 前會跑 pre-commit(ruff、gitleaks 等),CI 會再跑一次 lint、測試與 secret 掃描。
- Commit message 與 PR 標題用英文 Conventional Commits(`type: subject`,例如 `feat: add QR decoder`)。
- PR 需通過 CI 並經過 review 才能 merge,merge 用 squash。
- 樣本與輸出的處理規則見下方「資安規則」。

## 預算(上限 US$5)

- 預設不呼叫 LLM。QR 能解的欄位不送 LLM,只在 `--use-llm` 時補其他欄位。
- 單次執行最多 `RECEIPT_MAX_LLM_CALLS` 次呼叫(含重試,預設 5,上限 10)。這只是防呆;**真正的上限要在 OpenAI 後台為專用 key 設定**。
- 先用小模型,模型名稱由 `RECEIPT_MODEL` 指定,沒有預設值,避免默默用到貴的模型。
- 送出前圖片會縮到長邊 1600px 並重新編碼(同時去掉 EXIF)。

## 資安規則

- API key 只放本機 `.env`(已 ignore),不進 git、Issue、聊天。`.env.example` 只有空值。
- pre-commit(`pre-commit install`)跑 gitleaks,並擋下單據圖片、PDF、`result*.json`(連 `git add -f` 也擋)。`--no-verify` 能繞過,所以 CI 也要掃 secret(`.github/workflows/ci.yml`)。
- `.gitignore` 全 repo 擋 jpg/png/heic/pdf 與 `result*.json`。測試用的 QR 圖用 `qrcode` 即時產生,不放圖檔進 repo。
- 圖片上限:檔案 15MB、5000 萬像素。
- 樣本圖片與正確答案檔放 `samples/`(已 ignore),不 commit;說明見 `samples/README.md`。
- 輸出只寫 stdout,不自動寫檔;若要存檔,存到 repo 外或 `out/`(已 ignore)。
- log 只記次數與錯誤類型,不記 header、圖片、LLM 原始回應。
- QR 的 24 碼加密驗證資訊需賣方 AES 金鑰,**不驗證**,輸出也不宣稱「已驗證真偽」。
- 送第三方 LLM 前,供應商的資料保留與訓練政策要先查證並記在專案紀錄。程式用 `store=False`,但這**不等於 zero data retention**,供應商仍可能為 abuse monitoring 保留資料一段時間。
- 呼叫上限 `RECEIPT_MAX_LLM_CALLS` 限制在 1 到 10,且只算單次執行;**真正的上限是在 OpenAI 後台為專用 project 設定 budget limit**。

## TODO(之後的切片)

- QR 77 碼之後的品項明細解析(編碼參數 0 Big5 / 1 UTF-8 / 2 Base64)與右側 `**` QR。
- 只送裁切過的非 QR 區域給 LLM(資料最小化)。
- 20 張樣本的 benchmark:欄位正確率、延遲、成本。
