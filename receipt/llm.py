"""LLM client interface, retries, timeout and call budget. Not tied to one provider: implement Extractor to switch.

Security principles: never log request headers, image base64 or raw LLM responses;
LLM output is treated as data only, used after Pydantic schema validation, and is never executed as instructions or code.
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
    """Per-run LLM call limit (including retries). A sanity guard only; the real spend cap must be set in the provider dashboard."""

    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.used = 0

    def consume(self) -> None:
        if self.used >= self.max_calls:
            raise BudgetExceeded(f"LLM call limit per run reached ({self.max_calls})")
        self.used += 1


class Extractor(Protocol):
    def extract(self, image_data_url: str) -> LLMReceipt: ...


class OpenAIExtractor:
    def __init__(self, settings: Settings, budget: CallBudget, retries: int = 1):
        # max_retries=0: SDK-level retries silently cost extra, so retries are controlled here and counted against the budget
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
                    store=False,  # Not zero retention: the provider may still retain data for abuse monitoring; check its policy separately
                    max_output_tokens=1000,
                )
                if resp.output_parsed is None:
                    raise ValueError("empty parsed output")
                return resp.output_parsed
            except (ValidationError, ValueError, APITimeoutError, APIConnectionError, RateLimitError) as e:
                last_err = e
                # Log only the error type and attempt count, never the content
                log.warning("LLM call failed (attempt %d): %s", attempt + 1, type(e).__name__)
        raise RuntimeError("LLM extraction failed; fall back to manual review") from last_err
