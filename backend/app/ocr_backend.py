"""OCR backend integration layer supporting YomiToku and legacy engines."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, List

import cv2
import httpx
import numpy as np
from pdf2image import convert_from_path

from .utils import execute_concurrently, retry_with_backoff

logger = logging.getLogger(__name__)

_RAPID_OCR = None
_PADDLE_OCR = None

YOMITOKU_TIMEOUT = int(os.getenv("YOMITOKU_TIMEOUT", "60"))
YOMITOKU_MAX_WORKERS = int(os.getenv("YOMITOKU_MAX_WORKERS", "4"))
YOMITOKU_MAX_RETRIES = int(os.getenv("YOMITOKU_MAX_RETRIES", "3"))
YOMITOKU_RETRY_BASE_DELAY = float(os.getenv("YOMITOKU_RETRY_BASE_DELAY", "1.0"))
YOMITOKU_RETRY_MULTIPLIER = float(os.getenv("YOMITOKU_RETRY_MULTIPLIER", "2.0"))


class OCRResult(list):
    """List subclass containing OCR output along with backend metadata."""

    def __init__(self, texts: Iterable[str], backend_used: str) -> None:
        super().__init__(texts)
        self.backend_used = backend_used


class YomiTokuError(RuntimeError):
    """Custom error raised when YomiToku integration fails."""


def _preprocess(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        31,
        10,
    )
    coords = np.column_stack(np.where(thresh < 255))
    if coords.size > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (height, width) = thresh.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        thresh = cv2.warpAffine(
            thresh,
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
    return thresh


def _encode_png(image: np.ndarray) -> bytes:
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise YomiTokuError("Failed to encode page image to PNG for YomiToku.")
    return buffer.tobytes()


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


def _parse_yomitoku_payload(payload: dict, page_index: int) -> str:
    pages = payload.get("pages")
    if isinstance(pages, list) and pages:
        parts: List[str] = []
        for page in pages:
            if isinstance(page, dict):
                text = page.get("text", "")
                if text is None:
                    text = ""
                parts.append(str(text))
        return "\n".join(parts)
    text = payload.get("text")
    if text is not None:
        return str(text)
    raise YomiTokuError(
        f"YomiToku response for page {page_index + 1} did not contain 'pages' or 'text'."
    )


def _ocr_yomitoku_rest(images: List[np.ndarray], timeout: int = YOMITOKU_TIMEOUT, max_workers: int = YOMITOKU_MAX_WORKERS) -> List[str]:
    base_url = os.getenv("YOMITOKU_BASE_URL", "").strip()
    if not base_url:
        raise YomiTokuError("環境変数 YOMITOKU_BASE_URL が設定されていません。")
    endpoint = "/v1/ocr"
    api_key = os.getenv("YOMITOKU_API_KEY", "").strip()
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    base_url = base_url.rstrip("/")

    def worker(item: tuple[int, np.ndarray]) -> str:
        index, image = item

        def task() -> str:
            png_bytes = _encode_png(image)
            files = {"file": (f"page-{index + 1}.png", png_bytes, "image/png")}
            try:
                response = client.post(endpoint, files=files)
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                raise YomiTokuError(
                    f"YomiToku REST リクエストが失敗しました (page={index + 1}): {exc}"
                ) from exc
            if response.status_code >= 400:
                raise YomiTokuError(
                    f"YomiToku REST がエラーを返しました (status={response.status_code}, page={index + 1})."
                )
            try:
                payload = response.json()
            except ValueError as exc:
                raise YomiTokuError("YomiToku REST 応答が JSON ではありません。") from exc
            return _parse_yomitoku_payload(payload, index)

        return retry_with_backoff(
            task,
            attempts=YOMITOKU_MAX_RETRIES,
            base_delay=YOMITOKU_RETRY_BASE_DELAY,
            multiplier=YOMITOKU_RETRY_MULTIPLIER,
            exceptions=(YomiTokuError,),
            logger=logger,
        )

    with httpx.Client(base_url=base_url, timeout=timeout, headers=headers) as client:
        results = execute_concurrently(worker, list(enumerate(images)), max_workers=max_workers)
    return results


def _ocr_yomitoku_cli(images: List[np.ndarray], cli_path: str, max_workers: int = YOMITOKU_MAX_WORKERS) -> List[str]:
    cli_path = cli_path.strip()
    if not cli_path:
        raise YomiTokuError("環境変数 YOMITOKU_CLI_PATH が設定されていません。")

    def worker(item: tuple[int, np.ndarray]) -> str:
        index, image = item
        png_bytes = _encode_png(image)
        temp_file: tempfile.NamedTemporaryFile | None = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(png_bytes)
            temp_file.flush()
            temp_file.close()
            try:
                completed = subprocess.run(
                    [cli_path, "--image", temp_file.name],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=YOMITOKU_TIMEOUT,
                )
            except FileNotFoundError as exc:
                raise YomiTokuError(f"YomiToku CLI が見つかりません: {cli_path}") from exc
            except subprocess.TimeoutExpired as exc:
                raise YomiTokuError(f"YomiToku CLI がタイムアウトしました (page={index + 1})") from exc
            if completed.returncode != 0:
                stderr = (completed.stderr or "").strip()
                raise YomiTokuError(
                    f"YomiToku CLI がエラーを返しました (code={completed.returncode}, page={index + 1}): {stderr}"
                )
            stdout = (completed.stdout or "").strip()
            if not stdout:
                raise YomiTokuError(f"YomiToku CLI が空の応答を返しました (page={index + 1})。")
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError as exc:
                raise YomiTokuError("YomiToku CLI 応答が JSON ではありません。") from exc
            return _parse_yomitoku_payload(payload, index)
        finally:
            if temp_file is not None:
                try:
                    os.unlink(temp_file.name)
                except FileNotFoundError:
                    pass

    return execute_concurrently(worker, list(enumerate(images)), max_workers=max_workers)


def _run_batch_ocr(images: List[np.ndarray], runner) -> List[str]:
    texts: List[str] = []
    for image in images:
        texts.append(runner(image))
    return texts


def _run_yomitoku(images: List[np.ndarray]) -> tuple[List[str], str]:
    mode = os.getenv("YOMITOKU_MODE", "").strip().lower()
    if not mode:
        raise YomiTokuError("YOMITOKU_MODE が設定されていません。")

    if mode == "rest":
        texts = _ocr_yomitoku_rest(images)
        return texts, "yomitoku"
    if mode == "cli":
        cli_path = os.getenv("YOMITOKU_CLI_PATH", "")
        texts = _ocr_yomitoku_cli(images, cli_path)
        return texts, "yomitoku"
    raise YomiTokuError(f"未対応の YOMITOKU_MODE です: {mode}")


def ocr_pages(pdf_path: str, dpi: int = 350, backend: str = "yomitoku") -> OCRResult:
    backend = backend.lower()
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDFが見つかりません: {pdf_path}")

    pil_images = convert_from_path(str(path), dpi=dpi)
    raw_images: List[np.ndarray] = [cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR) for pil_image in pil_images]
    preprocessed_images: List[np.ndarray] = [_preprocess(image) for image in raw_images]

    backend_used = backend
    texts: List[str]

    if backend == "yomitoku":
        try:
            texts, backend_used = _run_yomitoku(raw_images)
        except YomiTokuError as exc:
            logger.warning("YomiToku の実行に失敗しました。RapidOCR にフォールバックします: %s", exc)
            backend_used = "rapidocr"
            texts = _run_batch_ocr(preprocessed_images, _run_rapidocr)
        else:
            total_length = sum(len(text.strip()) for text in texts)
            if total_length < 20:
                logger.warning(
                    "YomiToku の OCR 結果が少なすぎます (total_length=%s)。RapidOCR にフォールバックします。",
                    total_length,
                )
                backend_used = "rapidocr"
                texts = _run_batch_ocr(preprocessed_images, _run_rapidocr)
    elif backend == "rapidocr":
        texts = _run_batch_ocr(preprocessed_images, _run_rapidocr)
        backend_used = "rapidocr"
    elif backend == "paddleocr":
        texts = _run_batch_ocr(preprocessed_images, _run_paddleocr)
        backend_used = "paddleocr"
    else:
        raise ValueError("サポートされていないOCRバックエンドです。")

    return OCRResult(texts, backend_used)
