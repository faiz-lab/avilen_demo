from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    task_id: str


class StatusResponse(BaseModel):
    progress: int
    pages: int
    totals: dict


class RetryRequest(BaseModel):
    task_id: str
    token: str


class RetryResponse(BaseModel):
    candidates: List[str]


class ResultItem(BaseModel):
    pdf_name: str
    page: int
    token: str
    matched_type: Optional[str]
    matched_hinban: Optional[str]
    zaiko: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "ResultItem":
        return cls(**row)


class FailureItem(BaseModel):
    pdf_name: str
    page: int
    token: str

    @classmethod
    def from_row(cls, row: dict) -> "FailureItem":
        return cls(**row)
