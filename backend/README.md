# Backend - AI見積OCRシステム

このディレクトリには FastAPI ベースの OCR マッチング API が含まれます。`requirements.txt` を使用して依存関係をインストールし、`uvicorn app.main:app --reload` で起動してください。

アップロードするマスタ CSV には `hinban`・`kidou`・`zaiku` の 3 列が必須です。余分な列は読み込み時に無視され、必須列が不足している場合はエラー `CSVに必要な列（hinban, kidou, zaiku）が含まれていません。` を返します。

```
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows の場合は .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 環境依存

- Poppler: PDF→画像変換に利用します。macOS は `brew install poppler`、Ubuntu は `sudo apt update && sudo apt install poppler-utils` を実行してください。
- RapidOCR: `rapidocr-onnxruntime` が初回実行時にモデルをダウンロードします。ネットワークにアクセスできない環境では別途キャッシュをご用意ください。
- PaddleOCR: 任意で `pip install paddleocr` を追加し、API 経由で `ocr_backend=paddleocr` を指定すると切り替え可能です。

## 使用 YomiToku 作为 OCR 引擎

YomiToku (Document AI) を利用して OCR を実行するには、以下の環境変数を設定します。YomiToku が利用できない場合は RapidOCR に自動的にフォールバックします。

### REST 連携

```
export YOMITOKU_MODE=rest
export YOMITOKU_BASE_URL=http://localhost:8001
# 認証が必要な場合のみ
# export YOMITOKU_API_KEY=xxxxxx
```

各ページ画像を `POST {BASE_URL}/v1/ocr` に `multipart/form-data` として送信します。レスポンス JSON の `pages[].text` を統合してテキスト化します。

### CLI 連携

```
export YOMITOKU_MODE=cli
export YOMITOKU_CLI_PATH=/usr/local/bin/yomitoku
```

CLI 版は各ページの PNG を一時ファイルとして保存し、`<cli_path> --image <file>` で実行します。標準出力は JSON を想定しています。

### デフォルトバックエンドの選択とフォールバック

```
export OCR_BACKEND_DEFAULT=yomitoku
```

`/api/upload` の `ocr_backend` パラメータを省略すると `OCR_BACKEND_DEFAULT` が使われます。YomiToku が利用できない場合（接続エラー、CLI エラー、結果が極端に少ない等）は RapidOCR で自動的に再実行します。最終的に利用されたエンジンは `/api/status/{task_id}` の `backend_used` に反映されます。

### `.env` サンプル

```
OCR_BACKEND_DEFAULT=yomitoku
YOMITOKU_MODE=rest
YOMITOKU_BASE_URL=http://localhost:8001
# YOMITOKU_API_KEY=xxxxxx
# CLI を使用する場合:
# YOMITOKU_MODE=cli
# YOMITOKU_CLI_PATH=/usr/local/bin/yomitoku
```

## テスト

```
pytest
```
