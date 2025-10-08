# AI見積OCRシステム

PDF 図面や仕様書をローカル環境で OCR し、マスタ CSV と照合して結果 CSV を生成するフルスタック アプリケーションです。クラウド API を利用せず、RapidOCR (ONNXRuntime) または PaddleOCR を用いたオフライン処理を行います。

## 技術スタック

- Backend: Python 3.11+, FastAPI, Uvicorn, RapidOCR (ONNXRuntime) / PaddleOCR (任意)
- Frontend: Node.js 18+, Vite, React, TypeScript
- PDF & OCR: pdfplumber, pdf2image (Poppler), OpenCV, pandas

## 必要条件

- Python 3.11 以上
- Node.js 18 以上
- Poppler コマンド
  - **macOS**: `brew install poppler`
  - **Ubuntu**: `sudo apt update && sudo apt install poppler-utils`
- RapidOCR: `pip install -r backend/requirements.txt` に含まれます。初回実行時にモデルをローカルへキャッシュします。
- PaddleOCR (任意): `pip install paddleocr` を追加で実行し、フロントエンドの OCR エンジン選択を `PaddleOCR` に切り替えてください。

> **注意:** インターネットに接続できない環境では RapidOCR のモデルを事前にダウンロードして配置する必要があります。`~/.rapidocr/` に各モデルが保存されます。

## セットアップ手順

1. 仮想環境を準備します。

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

2. フロントエンド依存関係をインストールします。

   ```bash
   cd ../frontend
   npm install
   ```

3. バックエンドを起動します。

   ```bash
   cd ../backend
   uvicorn app.main:app --reload
   ```

4. フロントエンドを起動します。

   ```bash
   cd ../frontend
   npm run dev
   ```

5. ブラウザで `http://localhost:5173` を開きます。

## サンプルデータ

- `backend/app/sample_db.csv`: 品番 (`hinban`)・起動方式 (`kidou`)・在庫情報 (`zaiku`) を含むサンプルマスタ。
- `backend/app/sample_pdfs/spec_sheet_A.pdf`, `spec_sheet_B.pdf`: OCR 用テスト PDF。

## 使い方

1. 画面左側から `sample_db.csv` をアップロードします（CSV には `hinban`, `kidou`, `zaiku` 列が必須です）。
2. 複数 PDF をドラッグ＆ドロップで追加します。
3. 必要に応じて OCR エンジン (RapidOCR / PaddleOCR) を切り替えます。
4. 「処理を開始する」をクリックするとバックエンドで処理が開始されます。
5. 進捗バーと統計カードで状況を確認し、完了後「結果一覧」「失敗一覧」タブで内容を確認します。
6. 各タブ右上のボタンから `results.csv`・`failure.csv` をダウンロードできます。
7. 失敗行の「再照合」から修正トークンを入力し、再照合候補を確認できます。

## API エンドポイント

| Method | Path | 説明 |
| ------ | ---- | ---- |
| POST | `/api/upload` | CSV・PDF を受け取りタスクを生成します。|
| GET | `/api/status/{task_id}` | タスクの進捗と集計結果を返します。|
| GET | `/api/results/{task_id}` | マッチ結果を JSON で返します。|
| GET | `/api/failures/{task_id}` | 失敗トークンを JSON で返します。|
| POST | `/api/retry` | トークンを再照合し候補を返します。|
| GET | `/api/download/{task_id}?type=results|failures` | CSV ファイルをダウンロードします。|

## テスト

`normalize()` とトークン抽出ロジックの挙動を確認する軽量な pytest を同梱しています。

```bash
cd backend
pytest
```

## よくあるエラーと対処

| 症状 | 原因/対策 |
| ---- | --------- |
| `PDFの解析に失敗しました: ...` | Poppler が未インストールです。上記コマンドで導入してください。|
| `rapidocr-onnxruntime がインストールされていません` | `pip install -r backend/requirements.txt` の実行を確認してください。|
| OCR 実行時にモデルダウンロードが失敗 | オフライン環境ではモデルを事前取得し `~/.rapidocr/` に配置してください。|
| Permission Error (Windows) | コマンドプロンプトを管理者権限で実行し、保存先の権限を確認してください。|

## ライセンス

このリポジトリはデモ目的で提供されます。サンプルデータおよび生成された CSV は自由に改変して構いません。
