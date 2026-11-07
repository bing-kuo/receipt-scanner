"""Offline regressions using synthetic inputs and a fake LLM client."""

from types import SimpleNamespace

import pytest
import qrcode
from pydantic import SecretStr, ValidationError

from receipt import config, llm
from receipt.config import ConfigError, Settings
from receipt.llm import CallBudget, OpenAIExtractor
from receipt.models import LLMReceipt
from receipt.pipeline import NoQRFound, extract_receipt
from receipt.qr import parse_einvoice_left
from tests.conftest import FAKE_LEFT


@pytest.fixture
def settings_env(monkeypatch):
    monkeypatch.setattr(config, "find_dotenv", lambda **kwargs: "")
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-key")
    monkeypatch.setenv("RECEIPT_MODEL", "synthetic-model")
    monkeypatch.setenv("RECEIPT_MAX_LLM_CALLS", "5")


@pytest.mark.parametrize("value", ["nan", "NaN", "inf", "-inf", "1e309", "0", "-0", "-1"])
def test_timeout_rejects_nonfinite_or_nonpositive(settings_env, monkeypatch, value):
    monkeypatch.setenv("RECEIPT_TIMEOUT_S", value)
    with pytest.raises(ConfigError) as exc:
        Settings.from_env()
    assert str(exc.value) == "RECEIPT_TIMEOUT_S must be a finite positive number"


@pytest.mark.parametrize("value", ["0.001", "30", "301", "1e100"])
def test_timeout_accepts_finite_positive_without_arbitrary_ceiling(settings_env, monkeypatch, value):
    monkeypatch.setenv("RECEIPT_TIMEOUT_S", value)
    assert Settings.from_env().timeout_s == float(value)


def test_empty_items_fake_client_preserves_nullable_scalars(monkeypatch):
    calls = []

    def parse(**kwargs):
        calls.append(kwargs)
        assert "items: set [] (an empty list), never null." in kwargs["instructions"]
        assert "Return null for scalar fields you cannot read; return [] for items." in kwargs["instructions"]
        payload = dict.fromkeys(["invoice_number", "date", "seller_tax_id", "seller_name", "total_amount"])
        payload["items"] = []
        return SimpleNamespace(output_parsed=kwargs["text_format"].model_validate(payload))

    monkeypatch.setattr(
        llm, "OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse))
    )
    budget = CallBudget(2)
    extractor = OpenAIExtractor(Settings(SecretStr("synthetic-key"), "synthetic-model"), budget)
    result = extractor.extract("data:image/jpeg;base64,c3ludGhldGlj")
    assert result.items == []
    assert all(value is None for name, value in result.model_dump().items() if name != "items")
    assert len(calls) == budget.used == 1
    assert LLMReceipt().items == []
    with pytest.raises(ValidationError):
        LLMReceipt.model_validate({"items": None})


@pytest.mark.parametrize(
    "number",
    ["AB１２３４５６７８", "AB١٢٣٤٥٦٧٨", "AB1234567８", "ＡＢ12345678", "ab12345678", "A112345678"],
)
def test_qr_only_rejects_non_ascii_or_invalid_invoice_number(number):
    text = number + FAKE_LEFT[10:]
    assert parse_einvoice_left(text) is None
    image = qrcode.make(text, box_size=8, border=4).convert("RGB")
    with pytest.raises(NoQRFound):
        extract_receipt(image)


def test_qr_only_accepts_ascii_invoice_number(fake_invoice_image):
    assert extract_receipt(fake_invoice_image).invoice_number == "AB12345678"
