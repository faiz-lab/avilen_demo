import io
import pandas as pd

REQUIRED_COLUMNS = ["hinban", "kidou", "zaiku"]


def load_db_csv(data: bytes) -> pd.DataFrame:
    """从上传的CSV文件中读取必要列"""
    df: pd.DataFrame | None = None
    for enc in ("utf-8-sig", "cp932", "shift_jis", "utf-8"):
        try:
            df = pd.read_csv(
                io.BytesIO(data),
                encoding=enc,
                dtype=str,
                keep_default_na=False,
                na_filter=False,
                low_memory=False,
            )
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise ValueError("CSVの文字コードを判別できません。UTF-8 で保存してください。")

    cols = [c.lower().strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in cols]
    if missing:
        raise ValueError("CSVに必要な列（hinban, kidou, zaiku）が含まれていません。")

    # 只保留需要的列
    df = df[[c for c in df.columns if c.lower().strip() in REQUIRED_COLUMNS]].copy()

    rename_map = {c: c.lower().strip() for c in df.columns}
    df.rename(columns=rename_map, inplace=True)
    return df
