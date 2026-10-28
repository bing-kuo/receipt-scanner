"""LLM client 的介面、重試、timeout 與呼叫上限。供應商不綁死:換家只要實作 Extractor。

安全原則(Marcus M-3/M-5):不記錄 request header、圖片 base64、LLM 原始回應;
LLM 回傳只當資料,被 Pydantic schema 驗證後才使用,不會被當成指令或程式碼執行。
"""

import logging
from typing import Protocol

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from pydantic import ValidationError

from receipt.config import Settings
from receipt.models import LLMReceipt
from receipt.prompts import build_instructions

log = logging.getLogger(__name__)


class BudgetExceeded(RuntimeError):
    pass


class CallBudget:
    """單次執行的 LLM 呼叫上限(含重試)。這只是防呆;真正的金額上限要在供應商後台設。"""

    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.used = 0

    def consume(self) -> None:
        if self.used >= self.max_calls:
            raise BudgetExceeded(f"已達單次執行的 LLM 呼叫上限({self.max_calls})")
        self.used += 1


class Extractor(Protocol):
    def extract(self, image_data_url: str) -> LLMReceipt: ...


class OpenAIExtractor:
    def __init__(self, settings: Settings, budget: CallBudget, retries: int = 1):
        # max_retries=0:SDK 內建重試會偷偷多花錢,重試統一由這裡控制並計入 budget
        self._client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value(), timeout=settings.timeout_s, max_retries=0
        )
        self._model = settings.model
        self._budget = budget
        self._retries = retries

    def extract(self, image_data_url: str) -> LLMReceipt:
        instructions = build_instructions()
        last_err: Exception | None = None
        for attempt in range(self._retries + 1):
            self._budget.consume()
            try:
                resp = self._client.responses.parse(
                    model=self._model,
                    instructions=instructions,
                    input=[
                        {"role": "user", "content": [{"type": "input_image", "image_url": image_data_url}]}
                    ],
                    text_format=LLMReceipt,
                    store=False,  # 不等於 zero retention:供應商仍可能為 abuse monitoring 保留,需另查政策
                    max_output_tokens=1000,
                )
                if resp.output_parsed is None:
                    raise ValueError("empty parsed output")
                return resp.output_parsed
            except (ValidationError, ValueError, APITimeoutError, APIConnectionError, RateLimitError) as e:
                last_err = e
                # 只記錄錯誤類型與次數,不記錄內容
                log.warning("LLM call failed (attempt %d): %s", attempt + 1, type(e).__name__)
        raise RuntimeError("LLM 抽取失敗,建議退回人工") from last_err
