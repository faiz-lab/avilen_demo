import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.match import extract_tokens, normalize  # noqa: E402


def test_normalize_converts_fullwidth_and_case():
    assert normalize('ａｂ－１２３ｃ') == 'AB-123C'


def test_extract_tokens_filters_blacklist():
    text = 'SCALE 2024\n新規モデル: AB-1234'
    tokens = extract_tokens(text)
    assert 'AB-1234' in tokens
    assert 'SCALE' not in tokens
