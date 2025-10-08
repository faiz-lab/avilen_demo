from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

import pdfplumber

from .ocr_backend import OCRResult, ocr_pages

logger = logging.getLogger(__name__)


def extract_text_with_pdfplumber(pdf_path: Path) -> List[str]:
    texts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            texts.append(text)
    return texts


def extract_pdf_text(pdf_path: Path, backend: str = "yomitoku") -> Tuple[List[str], str]:
    pdf_texts = extract_text_with_pdfplumber(pdf_path)
    joined = "".join(pdf_texts).strip()
    if len(joined) >= 20:
        logger.info("Using text layer for %s", pdf_path)
        return pdf_texts, "text-layer"

    logger.info("Falling back to OCR for %s", pdf_path)
    try:
        result: OCRResult = ocr_pages(str(pdf_path), backend=backend)
        texts = list(result)
        backend_used = getattr(result, "backend_used", backend)
        return texts, backend_used
    except Exception as exc:  # pragma: no cover
        logger.exception("OCR failed for %s: %s", pdf_path, exc)
        raise RuntimeError(
            "OCR処理に失敗しました。RapidOCR/PaddleOCR の依存関係や Poppler のインストールを確認してください。"
        ) from exc
