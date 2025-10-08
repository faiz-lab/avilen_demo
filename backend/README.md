# Backend - AI見積OCRシステム

このディレクトリには FastAPI ベースの OCR マッチング API が含まれます。`requirements.txt` を使用して依存関係をインストールし、`uvicorn app.main:app --reload` で起動してください。

```
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows の場合は .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 環境依存

- Poppler: PDF→画像変換に利用します。macOS は `brew install poppler`、Ubuntu は `sudo apt update && sudo apt install poppler-utils` を実行してください。
- RapidOCR: `rapidocr-onnxruntime` が初回実行時にモデルをダウンロードします。ネットワークにアクセスできない環境では別途キャッシュをご用意ください。
- PaddleOCR: 任意で `pip install paddleocr` を追加し、API 経由で `ocr_backend=paddleocr` を指定すると切り替え可能です。

## テスト

```
pytest
```
