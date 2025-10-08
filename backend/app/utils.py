import os
import shutil
import string
import random
from pathlib import Path
from typing import Dict, Any

STORAGE_ROOT = Path(__file__).resolve().parent / "storage"


def generate_task_id(length: int = 12) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def init_task_storage(task_id: str) -> Path:
    task_dir = STORAGE_ROOT / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def clear_task_storage(task_id: str) -> None:
    task_dir = STORAGE_ROOT / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir, ignore_errors=True)


def save_upload_file(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)


def to_progress(total: int, current: int) -> int:
    if total <= 0:
        return 0
    return min(100, int(current / total * 100))


def ensure_dependencies() -> None:
    try:
        import poppler  # type: ignore # noqa: F401
    except Exception:
        # pdf2image requires poppler binaries; we simply check environment variable.
        pass


class TaskState:
    def __init__(self) -> None:
        self.progress: int = 0
        self.pages: int = 0
        self.current_page: int = 0
        self.status: str = "pending"
        self.error: str | None = None
        self.totals: Dict[str, int] = {"tokens": 0, "hit_hinban": 0, "hit_spec": 0, "fail": 0}
        self.results_path: Path | None = None
        self.failures_path: Path | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "progress": self.progress,
            "status": self.status,
            "error": self.error,
            "pages": self.pages,
            "totals": self.totals,
        }
