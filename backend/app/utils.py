"""Utility helpers for storage, task management, and concurrency."""
from __future__ import annotations

import random
import shutil
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Iterable, List, Sequence, TypeVar, cast

STORAGE_ROOT = Path(__file__).resolve().parent / "storage"

T = TypeVar("T")
R = TypeVar("R")


def generate_task_id(length: int = 12) -> str:
    """Generate a random task identifier."""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def init_task_storage(task_id: str) -> Path:
    """Create the storage directory for a task if it does not exist."""
    task_dir = STORAGE_ROOT / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def clear_task_storage(task_id: str) -> None:
    """Remove all files associated with a task."""
    task_dir = STORAGE_ROOT / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir, ignore_errors=True)


def save_upload_file(dest: Path, data: bytes) -> None:
    """Persist an uploaded file to disk."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as file:
        file.write(data)


def to_progress(total: int, current: int) -> int:
    """Convert a (total, current) pair into a percentage value."""
    if total <= 0:
        return 0
    return min(100, int(current / total * 100))


def ensure_dependencies() -> None:
    """Placeholder to ensure optional system level dependencies exist."""
    try:
        import poppler  # type: ignore # noqa: F401
    except Exception:
        # pdf2image requires poppler binaries; this check is intentionally lenient.
        pass


def execute_concurrently(
    func: Callable[[T], R],
    items: Sequence[T],
    *,
    max_workers: int = 4,
) -> List[R]:
    """Execute *func* for each item using a thread pool and preserve order.

    Args:
        func: Callable executed for each item.
        items: Items to process.
        max_workers: Maximum number of threads to use.

    Returns:
        List of results aligned with the order of *items*.
    """

    if not items:
        return []

    worker_count = max(1, min(max_workers, len(items)))
    results: List[Any] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {executor.submit(func, item): idx for idx, item in enumerate(items)}
        for future in as_completed(future_map):
            idx = future_map[future]
            results[idx] = future.result()
    return [cast(R, result) for result in results]


def retry_with_backoff(
    func: Callable[[], R],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    exceptions: Iterable[type[BaseException]] = (Exception,),
    logger: Any | None = None,
) -> R:
    """Execute *func* with exponential backoff retries.

    Args:
        func: Callable without arguments to execute.
        attempts: Maximum number of attempts.
        base_delay: Initial delay between attempts.
        multiplier: Multiplicative factor for the delay.
        exceptions: Exception types that trigger a retry.
        logger: Optional logger for retry messages.

    Raises:
        The last exception if all attempts fail.
    """

    delay = base_delay
    last_exc: BaseException | None = None
    exception_tuple = tuple(exceptions)

    for attempt in range(1, attempts + 1):
        try:
            return func()
        except exception_tuple as exc:  # type: ignore[arg-type]
            last_exc = exc
            if attempt >= attempts:
                raise
            if logger is not None:
                logger.warning("Retrying after error (attempt %s/%s): %s", attempt, attempts, exc)
            time.sleep(delay)
            delay *= multiplier
    # This should be unreachable because either func returned or the loop raised.
    if last_exc is not None:  # pragma: no cover
        raise last_exc
    raise RuntimeError("retry_with_backoff failed without capturing an exception")  # pragma: no cover


class TaskState:
    """In-memory state container for background OCR tasks."""

    def __init__(self) -> None:
        self.progress: int = 0
        self.pages: int = 0
        self.current_page: int = 0
        self.status: str = "pending"
        self.error: str | None = None
        self.totals: dict[str, int] = {
            "tokens": 0,
            "hit_hinban": 0,
            "hit_spec": 0,
            "fail": 0,
        }
        self.results_path: Path | None = None
        self.failures_path: Path | None = None
        self.backend_requested: str | None = None
        self.backend_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the task state to a serialisable dictionary."""
        return {
            "progress": self.progress,
            "status": self.status,
            "error": self.error,
            "pages": self.pages,
            "totals": self.totals,
            "backend_requested": self.backend_requested,
            "backend_used": self.backend_used,
        }
