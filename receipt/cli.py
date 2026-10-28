import argparse
import logging
import os
import sys
from pathlib import Path

from openai import APIError

from receipt.config import ConfigError, Settings
from receipt.imageio import ImageError, load_image
from receipt.llm import BudgetExceeded, CallBudget, OpenAIExtractor
from receipt.pipeline import NoQRFound, extract_receipt


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="receipt", description="Receipt recognition PoC")
    sub = p.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract", help="圖片進、JSON 出(stdout)")
    ex.add_argument("image", type=Path)
    ex.add_argument("--use-llm", action="store_true", help="呼叫 LLM 補欄位(會花錢,預設關閉)")
    ex.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    os.umask(0o077)  # 之後若寫檔,預設只有自己可讀
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, stream=sys.stderr)
    try:
        image = load_image(args.image)
        extractor = None
        if args.use_llm:
            settings = Settings.from_env()
            extractor = OpenAIExtractor(settings, CallBudget(settings.max_llm_calls))
        receipt = extract_receipt(image, extractor)
    except (ImageError, ConfigError, NoQRFound, BudgetExceeded, NotImplementedError, RuntimeError) as e:
        print(f"錯誤:{e}", file=sys.stderr)
        return 2
    except (APIError, ValueError) as e:
        # 只印例外類型與 HTTP status,不印訊息:之後訊息可能夾帶 request/response 內容
        status = getattr(e, "status_code", None)
        print(f"錯誤:{type(e).__name__}" + (f"(HTTP {status})" if status else ""), file=sys.stderr)
        return 2
    print(receipt.model_dump_json(indent=2))
    return 0
