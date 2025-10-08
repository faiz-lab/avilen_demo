from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import cv2
import numpy as np
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

_RAPID_OCR = None
_PADDLE_OCR = None


def _preprocess(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY, 31, 10)
    coords = np.column_stack(np.where(thresh < 255))
    if coords.size > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = thresh.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        thresh = cv2.warpAffine(thresh, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return thresh


def _get_rapid_ocr():
    global _RAPID_OCR
    if _RAPID_OCR is None:
        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("rapidocr-onnxruntime がインストールされていません。") from exc
        _RAPID_OCR = RapidOCR()
    return _RAPID_OCR


def _get_paddle_ocr():
    global _PADDLE_OCR
    if _PADDLE_OCR is None:
        try:
            from paddleocr import PaddleOCR  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "PaddleOCR がインストールされていません。pip install paddleocr を実行してください。"
            ) from exc
        _PADDLE_OCR = PaddleOCR(use_angle_cls=True, lang="japan", show_log=False)
    return _PADDLE_OCR


def _run_rapidocr(image: np.ndarray) -> str:
    engine = _get_rapid_ocr()
    result, _ = engine(image)
    if not result:
        return ""
    return " ".join([line[1] for line in result])


def _run_paddleocr(image: np.ndarray) -> str:
    engine = _get_paddle_ocr()
    result = engine.ocr(image, cls=True)
    texts: List[str] = []
    for line in result:
        if line and len(line) > 0:
            texts.append(line[1][0])
    return " ".join(texts)


def ocr_pages(pdf_path: str, dpi: int = 350, backend: str = "rapidocr") -> List[str]:
    backend = backend.lower()
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDFが見つかりません: {pdf_path}")

    images = convert_from_path(str(path), dpi=dpi)
    texts: List[str] = []
    for pil_image in images:
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        processed = _preprocess(image)
        if backend == "rapidocr":
            page_text = _run_rapidocr(processed)
        elif backend == "paddleocr":
            page_text = _run_paddleocr(processed)
        else:
            raise ValueError("サポートされていないOCRバックエンドです。")
        texts.append(page_text)
    return texts
