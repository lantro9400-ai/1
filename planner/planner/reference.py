"""레퍼런스 기획안 → Claude 입력 블록.

- PDF: 그대로 document 블록으로 보낸다. Claude 는 PDF 각 페이지를 이미지로도 보기 때문에
  텍스트 레이어가 없는 이미지형 PDF(지난 김장 편 같은)도 읽을 수 있다.
  단, 요청 한도(32MB)를 넘으면 pdftoppm 으로 페이지를 JPEG 로 렌더링해서 이미지 블록으로 보낸다.
- PNG/JPG: 이미지 블록.
- JSON (archive/.../plan.json): 텍스트로 프롬프트에 넣는다 (prompt.build_user_text).
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

PDF_LIMIT_BYTES = 30 * 1024 * 1024
MAX_IMAGES = 60
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _b64(data: bytes) -> str:
    return base64.standard_b64encode(data).decode("ascii")


def _render_pdf_pages(path: Path) -> list[dict[str, Any]]:
    if not shutil.which("pdftoppm"):
        raise SystemExit("PDF 가 너무 커서 페이지 렌더링이 필요한데 pdftoppm(poppler)이 없습니다.")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["pdftoppm", "-jpeg", "-r", "80", "-scale-to", "1568", str(path), f"{tmp}/p"],
            check=True,
        )
        pages = sorted(Path(tmp).glob("p*.jpg"))[:MAX_IMAGES]
        return [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _b64(p.read_bytes())}}
            for p in pages
        ]


def reference_blocks(paths: list[Path]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            data = path.read_bytes()
            if len(data) <= PDF_LIMIT_BYTES:
                blocks.append(
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": _b64(data)},
                        "title": path.name,
                    }
                )
            else:
                blocks.extend(_render_pdf_pages(path))
        elif suffix in IMAGE_TYPES:
            blocks.append(
                {"type": "image", "source": {"type": "base64", "media_type": IMAGE_TYPES[suffix], "data": _b64(path.read_bytes())}}
            )
        elif suffix == ".json":
            continue  # 텍스트로 처리
        else:
            raise SystemExit(f"지원하지 않는 레퍼런스 형식입니다: {path.name} (PDF/PNG/JPG/JSON)")
    return blocks


def reference_json_text(paths: list[Path]) -> str | None:
    texts = [p.read_text(encoding="utf-8") for p in paths if p.suffix.lower() == ".json"]
    return "\n\n".join(texts) if texts else None
