from __future__ import annotations
from typing import Dict, List, Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    task_id: str


class StatusResponse(BaseModel):
    progress: int
    pages: int
    totals: Dict[str, int]
    backend_used: Optional[str] = None


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
