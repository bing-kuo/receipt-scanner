"""圖片載入與縮圖。圖片是不可信輸入:限制檔案大小,並在送出前重新編碼(順便去掉 EXIF,例如 GPS)。"""

import base64
import io
from pathlib import Path

from PIL import Image, ImageOps

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 50_000_000  # 15MB 的 PNG 可能解壓成上億像素,先看 header 的尺寸
LLM_MAX_SIDE = 1600  # 送 LLM 前縮圖,降低 token 成本;可依 benchmark 調整


class ImageError(ValueError):
    pass


def load_image(path: Path) -> Image.Image:
    try:
        size = path.stat().st_size
    except OSError as e:
        raise ImageError("找不到檔案") from e
    if size > MAX_FILE_BYTES:
        raise ImageError(f"檔案超過 {MAX_FILE_BYTES // (1024 * 1024)}MB 上限")
    try:
        with Image.open(path) as im:
            if im.width * im.height > MAX_PIXELS:
                raise ImageError("圖片像素過大")
            im = ImageOps.exif_transpose(im)
            return im.convert("RGB")
    except ImageError:
        raise
    except Exception as e:  # Pillow 對壞檔的例外種類很多
        raise ImageError("無法讀取圖片") from e


def to_data_url(image: Image.Image, max_side: int = LLM_MAX_SIDE) -> str:
    im = image.copy()
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)  # 重新編碼,不帶 EXIF
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
