from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Set, TYPE_CHECKING

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
    df: "pd.DataFrame"
    hinban_set: Set[str]


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


def build_database_index(df: "pd.DataFrame") -> DatabaseIndex:
    frame = df.copy()
    frame["hinban"] = frame["hinban"].fillna("")
    frame["kidou"] = frame["kidou"].fillna("")
    frame["zaiku"] = frame["zaiku"].fillna("")
    frame["HINBAN_N"] = frame["hinban"].apply(normalize)
    hinban_set: Set[str] = set(frame["HINBAN_N"])
    return DatabaseIndex(df=frame, hinban_set=hinban_set)


def match_token_to_db(token: str, index: DatabaseIndex) -> Dict[str, object]:
    token_n = normalize(token)
    if token_n in index.hinban_set:
        row = index.df.loc[index.df["HINBAN_N"] == token_n].iloc[0]
        return {
            "matched": True,
            "hinban": row["hinban"],
            "kidou": row["kidou"],
            "zaiku": row["zaiku"],
        }
    return {"matched": False}
