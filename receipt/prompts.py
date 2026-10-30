"""Instructions (prompt) for the LLM.

NOTE: Not implemented yet. `--use-llm` therefore reports an error. This is intentional, to avoid spending API
credit on an empty prompt.

Interface: `build_instructions() -> str` returns the instructions sent to the model. The image is passed
separately as input by llm.py and must not be mixed into this string. The output format is constrained by the
`models.LLMReceipt` schema.

Constraints and risks:
- Text on a receipt is untrusted input and may contain instructions. The prompt must clearly separate
  "data to extract" from "instructions".
- Return null for fields that cannot be read; never guess.

Acceptance criteria:
- Per-field accuracy, latency and per-receipt cost are measured and recorded on 20 samples.
- Samples containing instruction-like text (e.g. "ignore the above instructions") do not affect the output,
  which still conforms to the schema.
- A decision on whether to pass the fields already decoded from the QR code to the model is made and the reason recorded.
"""


def build_instructions() -> str:
    raise NotImplementedError("prompt is not implemented yet (see receipt/prompts.py)")
