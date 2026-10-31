"""Settings are read from environment variables (loaded from .env in local development). The key is never printed or logged."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from pydantic import SecretStr

MIN_CALLS, MAX_CALLS_CEILING = (
    1,
    10,
)  # Sanity bounds only; the real spend cap must be set in the OpenAI dashboard


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    # SecretStr: repr, str, asdict and vars only show **********; call get_secret_value() only when creating the client
    openai_api_key: SecretStr = field(repr=False)
    model: str
    timeout_s: float = 30.0
    max_llm_calls: int = (
        5  # Per-run call limit (including retries) to prevent runaway loops from burning money
    )

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()  # Load .env from the current directory; skip if missing
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        model = os.environ.get("RECEIPT_MODEL", "").strip()
        if not key:
            raise ConfigError("OPENAI_API_KEY is not set; copy .env.example to .env and fill it in.")
        if not model:
            raise ConfigError(
                "RECEIPT_MODEL is not set; specify a small model with image input support in .env."
            )
        try:
            timeout_s = float(os.environ.get("RECEIPT_TIMEOUT_S", "30"))
            max_calls = int(os.environ.get("RECEIPT_MAX_LLM_CALLS", "5"))
        except ValueError as e:
            raise ConfigError("RECEIPT_TIMEOUT_S or RECEIPT_MAX_LLM_CALLS is not a valid number") from e
        return cls(
            openai_api_key=SecretStr(key),
            model=model,
            timeout_s=timeout_s,
            max_llm_calls=min(max(max_calls, MIN_CALLS), MAX_CALLS_CEILING),
        )
