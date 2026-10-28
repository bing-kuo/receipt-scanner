"""設定一律從環境變數讀(本機開發時由 .env 載入)。不印出、不記錄 key。"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from pydantic import SecretStr

MIN_CALLS, MAX_CALLS_CEILING = 1, 10  # 防呆邊界;真正的金額上限要在 OpenAI 後台設


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    # SecretStr:repr、str、asdict、vars 都只會顯示 **********;只在建立 client 時 get_secret_value()
    openai_api_key: SecretStr = field(repr=False)
    model: str
    timeout_s: float = 30.0
    max_llm_calls: int = 5  # 單次執行的呼叫上限(含重試),防止迴圈燒錢

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()  # 讀取目前目錄的 .env;不存在就略過
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        model = os.environ.get("RECEIPT_MODEL", "").strip()
        if not key:
            raise ConfigError("OPENAI_API_KEY 未設定,請複製 .env.example 為 .env 並填入。")
        if not model:
            raise ConfigError("RECEIPT_MODEL 未設定,請在 .env 指定一個小型、支援圖片輸入的模型。")
        try:
            timeout_s = float(os.environ.get("RECEIPT_TIMEOUT_S", "30"))
            max_calls = int(os.environ.get("RECEIPT_MAX_LLM_CALLS", "5"))
        except ValueError as e:
            raise ConfigError("RECEIPT_TIMEOUT_S 或 RECEIPT_MAX_LLM_CALLS 不是有效數字") from e
        return cls(
            openai_api_key=SecretStr(key),
            model=model,
            timeout_s=timeout_s,
            max_llm_calls=min(max(max_calls, MIN_CALLS), MAX_CALLS_CEILING),
        )
