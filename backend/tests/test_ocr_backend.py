from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("cv2")

from app import ocr_backend


class _ArrayImage:
    def __init__(self, array):
        self._array = array

    def __array__(self):  # pragma: no cover - simple adapter
        return self._array


def _create_dummy_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 10 10]/Contents 4 0 R/Resources<</ProcSet[/PDF/Text]/Font<</F1 5 0 R>>>>>>endobj\n4 0 obj<</Length 44>>stream\nBT /F1 8 Tf 1 0 0 1 2 5 Tm (dummy) Tj ET\nendstream\nendobj\n5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\nxref\n0 6\n0000000000 65535 f \n0000000015 00000 n \n0000000062 00000 n \n0000000115 00000 n \n0000000274 00000 n \n0000000372 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n434\n%%EOF\n")


def test_yomitoku_falls_back_to_rapid(monkeypatch, tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    _create_dummy_pdf(pdf_path)

    monkeypatch.delenv("YOMITOKU_MODE", raising=False)

    sample_array = ocr_backend.np.full((10, 10, 3), 255, dtype=ocr_backend.np.uint8)

    def fake_convert_from_path(path: str, dpi: int = 350):  # type: ignore[override]
        return [_ArrayImage(sample_array)]

    def fake_preprocess(image):  # type: ignore[override]
        return image

    def fake_rapidocr(image):  # type: ignore[override]
        return "rapid-text"

    monkeypatch.setattr(ocr_backend, "convert_from_path", fake_convert_from_path)
    monkeypatch.setattr(ocr_backend, "_preprocess", fake_preprocess)
    monkeypatch.setattr(ocr_backend, "_run_rapidocr", fake_rapidocr)

    result = ocr_backend.ocr_pages(str(pdf_path), backend="yomitoku")

    assert list(result) == ["rapid-text"]
    assert getattr(result, "backend_used") == "rapidocr"
