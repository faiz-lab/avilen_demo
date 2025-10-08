from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

TOKEN_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9\-_\/]{3,}")
BLACKLIST = {
    "SCALE",
    "DATE",
    "PAGE",
    "SIZE",
    "ISO",
    "DIN",
    "MM",
    "KG",
    "LOT",
    "MODEL",
    "CODE",
    "FAX",
    "TEL",
}


@dataclass
class DatabaseIndex:
    frame: 'pd.DataFrame'
    hinban_map: Dict[str, List[int]]


def normalize(value: str) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.upper()
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"[\s\u3000]+", " ", text)
    return text.strip()


def extract_tokens(text: str) -> List[str]:
    if not text:
        return []
    cleaned = normalize(text)
    candidates = set()
    for match in TOKEN_PATTERN.findall(cleaned):
        if any(ch.isdigit() for ch in match) and match not in BLACKLIST:
            candidates.add(match)
    return sorted(candidates)


def build_database_index(df: 'pd.DataFrame') -> DatabaseIndex:
    import pandas as pd  # type: ignore

    if "hinban" not in df.columns or "spec" not in df.columns:
        raise ValueError("CSVに 'hinban' および 'spec' 列が必要です。")

    frame = df.copy()
    frame["HINBAN_N"] = frame["hinban"].fillna("").apply(normalize)
    frame["SPEC_N"] = frame["spec"].fillna("").apply(normalize)

    hinban_map: Dict[str, List[int]] = {}
    for idx, value in frame["HINBAN_N"].items():
        if not value:
            continue
        hinban_map.setdefault(value, []).append(idx)

    return DatabaseIndex(frame=frame, hinban_map=hinban_map)


def match_token(token: str, index: DatabaseIndex) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    normalized_token = normalize(token)

    if normalized_token in index.hinban_map:
        for row_idx in index.hinban_map[normalized_token]:
            row = index.frame.loc[row_idx]
            result = {
                "matched_type": "hinban",
                "matched_hinban": row.get("hinban", ""),
            }
            if "zaiko" in row:
                result["zaiko"] = row.get("zaiko")
            results.append(result)
        return results

    spec_matches = index.frame[index.frame["SPEC_N"].str.contains(normalized_token, na=False)]
    for _, row in spec_matches.iterrows():
        result = {
            "matched_type": "spec",
            "matched_hinban": row.get("hinban", ""),
        }
        if "zaiko" in row:
            result["zaiko"] = row.get("zaiko")
        results.append(result)
    return results
