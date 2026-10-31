"""Image loading and resizing. Images are untrusted input: cap the file size and re-encode before sending (which also strips EXIF, e.g. GPS)."""

import base64
import io
from pathlib import Path

from PIL import Image, ImageOps

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 50_000_000  # A 15MB PNG can decompress to hundreds of millions of pixels, so check the header dimensions first
LLM_MAX_SIDE = 1600  # Downscale before sending to the LLM to reduce token cost; tune based on benchmarks


class ImageError(ValueError):
    pass


def load_image(path: Path) -> Image.Image:
    try:
        size = path.stat().st_size
    except OSError as e:
        raise ImageError("file not found") from e
    if size > MAX_FILE_BYTES:
        raise ImageError(f"file exceeds the {MAX_FILE_BYTES // (1024 * 1024)}MB limit")
    try:
        with Image.open(path) as im:
            if im.width * im.height > MAX_PIXELS:
                raise ImageError("image has too many pixels")
            im = ImageOps.exif_transpose(im)
            return im.convert("RGB")
    except ImageError:
        raise
    except Exception as e:  # Pillow raises many different exception types for corrupt files
        raise ImageError("cannot read image") from e


def to_data_url(image: Image.Image, max_side: int = LLM_MAX_SIDE) -> str:
    im = image.copy()
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)  # Re-encode without EXIF
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
