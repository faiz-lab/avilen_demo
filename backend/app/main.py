from __future__ import annotations

import io
import logging
import os
import threading
from pathlib import Path
from typing import Dict, List

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .extract import extract_pdf_text
from .match import build_database_index, extract_tokens, match_token
from .models import RetryRequest, RetryResponse, StatusResponse, UploadResponse
from .utils import TaskState, generate_task_id, init_task_storage

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI見積OCRシステム API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TASKS: Dict[str, TaskState] = {}
TASK_LOCK = threading.Lock()
DB_PATHS: Dict[str, Path] = {}
RESULT_CACHE: Dict[str, List[Dict[str, str]]] = {}
FAILURE_CACHE: Dict[str, List[Dict[str, str]]] = {}

ALLOWED_OCR_BACKENDS = {"yomitoku", "rapidocr", "paddleocr"}


def _get_default_backend() -> str:
    default_backend = os.getenv("OCR_BACKEND_DEFAULT", "yomitoku").strip().lower()
    if default_backend not in ALLOWED_OCR_BACKENDS:
        logger.warning("Invalid OCR_BACKEND_DEFAULT=%s. Falling back to yomitoku.", default_backend)
        return "yomitoku"
    return default_backend


def _read_csv(data: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSVの文字コードを判別できません。UTF-8 で保存してください。")


def _process_task(
    task_id: str,
    db_bytes: bytes,
    pdf_entries: List[tuple[str, bytes]],
    ocr_backend: str,
) -> None:
    with TASK_LOCK:
        state = TASKS.get(task_id)
    if state is None:
        return

    state.backend_requested = ocr_backend

    task_dir = init_task_storage(task_id)
    try:
        df = _read_csv(db_bytes)
        index = build_database_index(df)
        db_path = task_dir / "database.csv"
        db_path.write_bytes(db_bytes)
        DB_PATHS[task_id] = db_path
    except Exception as exc:
        state.status = "error"
        state.error = f"CSVの解析に失敗しました: {exc}"
        logger.exception("Failed to load DB CSV: %s", exc)
        return

    pdf_texts: List[tuple[str, List[str]]] = []
    for name, data in pdf_entries:
        pdf_path = task_dir / name
        pdf_path.write_bytes(data)
        try:
            texts, backend_used = extract_pdf_text(pdf_path, backend=ocr_backend)
            state.backend_used = backend_used
        except RuntimeError as exc:
            state.status = "error"
            state.error = str(exc)
            return
        except Exception as exc:  # pragma: no cover
            state.status = "error"
            state.error = f"PDFの解析に失敗しました: {exc}"
            logger.exception("Failed to extract PDF: %s", exc)
            return
        pdf_texts.append((name, texts))
        state.pages += len(texts)

    results: List[Dict[str, str]] = []
    failures: List[Dict[str, str]] = []
    state.status = "processing"
    processed_pages = 0

    for pdf_name, pages in pdf_texts:
        for page_idx, page_text in enumerate(pages, start=1):
            tokens = extract_tokens(page_text)
            state.totals["tokens"] += len(tokens)
            for token in tokens:
                matches = match_token(token, index)
                if matches:
                    for match in matches:
                        record = {
                            "pdf_name": pdf_name,
                            "page": page_idx,
                            "token": token,
                            "matched_type": match.get("matched_type"),
                            "matched_hinban": match.get("matched_hinban"),
                        }
                        if match.get("matched_type") == "hinban":
                            state.totals["hit_hinban"] += 1
                        elif match.get("matched_type") == "spec":
                            state.totals["hit_spec"] += 1
                        if "zaiko" in match:
                            record["zaiko"] = match["zaiko"]
                        results.append(record)
                else:
                    failures.append(
                        {
                            "pdf_name": pdf_name,
                            "page": page_idx,
                            "token": token,
                        }
                    )
                    state.totals["fail"] += 1
            processed_pages += 1
            state.progress = int(min(100, (processed_pages / max(1, state.pages)) * 100))

    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df = results_df.sort_values(by=["pdf_name", "page", "matched_type"])
    results_path = task_dir / "results.csv"
    results_df.to_csv(results_path, index=False, encoding="utf-8-sig")
    RESULT_CACHE[task_id] = results_df.to_dict(orient="records") if not results_df.empty else []

    failures_df = pd.DataFrame(failures)
    if not failures_df.empty:
        failures_df = failures_df.sort_values(by=["pdf_name", "page"])
    failures_path = task_dir / "failure.csv"
    failures_df.to_csv(failures_path, index=False, encoding="utf-8-sig")
    FAILURE_CACHE[task_id] = failures_df.to_dict(orient="records") if not failures_df.empty else []

    state.results_path = results_path
    state.failures_path = failures_path
    state.progress = 100
    state.status = "completed"


@app.post("/api/upload", response_model=UploadResponse)
async def upload(
    db_csv: UploadFile = File(...),
    pdfs: List[UploadFile] = File(...),
    ocr_backend: str | None = None,
):
    if not pdfs:
        raise HTTPException(status_code=400, detail="PDFファイルを1件以上アップロードしてください。")

    requested_backend = (ocr_backend or _get_default_backend()).strip().lower()
    if requested_backend not in ALLOWED_OCR_BACKENDS:
        raise HTTPException(status_code=400, detail=f"未対応のOCRバックエンドです: {requested_backend}")

    task_id = generate_task_id()
    state = TaskState()
    with TASK_LOCK:
        TASKS[task_id] = state

    db_bytes = await db_csv.read()
    pdf_entries: List[tuple[str, bytes]] = []
    for pdf in pdfs:
        pdf_entries.append((pdf.filename or "document.pdf", await pdf.read()))

    thread = threading.Thread(
        target=_process_task,
        args=(task_id, db_bytes, pdf_entries, requested_backend),
        daemon=True,
    )
    thread.start()

    return UploadResponse(task_id=task_id)


@app.get("/api/status/{task_id}", response_model=StatusResponse)
async def status(task_id: str):
    state = TASKS.get(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="指定されたタスクIDが存在しません。")
    if state.status == "error":
        raise HTTPException(status_code=500, detail=state.error or "タスクでエラーが発生しました。")
    return StatusResponse(
        progress=state.progress,
        pages=state.pages,
        totals=state.totals,
        backend_used=state.backend_used,
    )


@app.get("/api/results/{task_id}")
async def get_results(task_id: str):
    state = TASKS.get(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません。")
    if state.status != "completed":
        raise HTTPException(status_code=400, detail="処理が完了していません。")
    return RESULT_CACHE.get(task_id, [])


@app.get("/api/failures/{task_id}")
async def get_failures(task_id: str):
    state = TASKS.get(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません。")
    if state.status != "completed":
        raise HTTPException(status_code=400, detail="処理が完了していません。")
    return FAILURE_CACHE.get(task_id, [])


@app.post("/api/retry", response_model=RetryResponse)
async def retry(request: RetryRequest):
    state = TASKS.get(request.task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません。")
    db_path = DB_PATHS.get(request.task_id)
    if db_path is None or not db_path.exists():
        raise HTTPException(status_code=400, detail="DBが利用できません。再度アップロードしてください。")

    df = pd.read_csv(db_path)
    index = build_database_index(df)
    matches = match_token(request.token, index)
    candidates = [m.get("matched_hinban") for m in matches if m.get("matched_hinban")]
    return RetryResponse(candidates=candidates)


@app.get("/api/download/{task_id}")
async def download(task_id: str, type: str):
    state = TASKS.get(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません。")
    if state.status != "completed":
        raise HTTPException(status_code=400, detail="処理が完了していません。")

    if type == "results" and state.results_path:
        return FileResponse(state.results_path, filename=f"{task_id}_results.csv", media_type="text/csv")
    if type == "failures" and state.failures_path:
        return FileResponse(state.failures_path, filename=f"{task_id}_failure.csv", media_type="text/csv")
    raise HTTPException(status_code=404, detail="CSVがまだ生成されていません。")
