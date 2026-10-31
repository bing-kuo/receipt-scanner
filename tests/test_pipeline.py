import pytest

from receipt.cli import main
from receipt.llm import BudgetExceeded, CallBudget
from receipt.models import LLMReceipt
from receipt.pipeline import NoQRFound, extract_receipt


class FakeExtractor:
    def __init__(self):
        self.calls = 0

    def extract(self, image_data_url: str) -> LLMReceipt:
        self.calls += 1
        assert image_data_url.startswith("data:image/jpeg;base64,")
        return LLMReceipt(seller_name="測試商店")


def test_qr_only_makes_no_llm_call(fake_invoice_image):
    r = extract_receipt(fake_invoice_image)
    assert r.total_amount == 80
    assert set(r.sources.values()) == {"qr"}


def test_no_qr_without_llm_fails_clearly(blank_image):
    with pytest.raises(NoQRFound):
        extract_receipt(blank_image)


def test_llm_path_goes_through_reconcile_stub(fake_invoice_image):
    # reconcile is not implemented yet; it must fail loudly rather than silently return a default answer
    ex = FakeExtractor()
    with pytest.raises(NotImplementedError):
        extract_receipt(fake_invoice_image, ex)
    assert ex.calls == 1


def test_budget_blocks_extra_calls():
    b = CallBudget(2)
    b.consume()
    b.consume()
    with pytest.raises(BudgetExceeded):
        b.consume()


def test_cli_qr_only(fake_invoice_image, tmp_path, capsys):
    p = tmp_path / "x.png"
    fake_invoice_image.save(p)
    assert main(["extract", str(p)]) == 0
    assert '"AB12345678"' in capsys.readouterr().out


def test_cli_llm_requires_key(fake_invoice_image, tmp_path, monkeypatch, capsys):
    p = tmp_path / "x.png"
    fake_invoice_image.save(p)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # avoid picking up a real local .env
    assert main(["extract", str(p), "--use-llm"]) == 2
    assert "OPENAI_API_KEY" in capsys.readouterr().err


def test_settings_secret_not_leaked(monkeypatch, tmp_path):
    import dataclasses

    from receipt.config import Settings

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-FAKEKEY")
    monkeypatch.setenv("RECEIPT_MODEL", "m")
    monkeypatch.setenv("RECEIPT_MAX_LLM_CALLS", "100000")
    s = Settings.from_env()
    for text in (repr(s), str(s), str(dataclasses.asdict(s)), str(vars(s))):
        assert "FAKEKEY" not in text
    assert s.max_llm_calls == 10  # clamp


def test_bad_numeric_env_is_config_error(fake_invoice_image, tmp_path, monkeypatch, capsys):
    p = tmp_path / "x.png"
    fake_invoice_image.save(p)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-FAKEKEY")
    monkeypatch.setenv("RECEIPT_MODEL", "m")
    monkeypatch.setenv("RECEIPT_TIMEOUT_S", "abc")
    assert main(["extract", str(p), "--use-llm"]) == 2
    assert "FAKEKEY" not in capsys.readouterr().err


def test_oversized_pixels_rejected(tmp_path, monkeypatch):
    from PIL import Image

    from receipt import imageio

    p = tmp_path / "big.png"
    Image.new("L", (300, 300)).save(p)
    monkeypatch.setattr(imageio, "MAX_PIXELS", 1000)
    with pytest.raises(imageio.ImageError, match="too many pixels"):
        imageio.load_image(p)
