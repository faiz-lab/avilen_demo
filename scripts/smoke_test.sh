#!/usr/bin/env bash
set -euo pipefail

API_BASE=${API_BASE:-http://127.0.0.1:8000}
FRONTEND_BASE=${FRONTEND_BASE:-http://127.0.0.1:5173}
SCRIPT_DIR=$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TMP_DIR=$(mktemp -d)
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

cp "$SCRIPT_DIR/fixtures/master.csv" "$TMP_DIR/db.csv"
cp "$SCRIPT_DIR/fixtures/sample.pdf" "$TMP_DIR/sample.pdf"

echo "[1/6] Uploading sample job to $API_BASE/api/upload"
UPLOAD_RESPONSE=$(curl -sS -f \
  -F "db_csv=@$TMP_DIR/db.csv" \
  -F "pdfs=@$TMP_DIR/sample.pdf" \
  -F "ocr_backend=yomitoku" \
  "$API_BASE/api/upload")

task_id=$(python - <<'PY'
import json, os
payload = json.loads(os.environ['UPLOAD_RESPONSE'])
print(payload['task_id'])
PY
)

echo "    → task_id=$task_id"

echo "[2/6] Polling status until completion"
for attempt in {1..30}; do
  STATUS_JSON=$(curl -sS "$API_BASE/api/status/$task_id") || true
  progress=$(python - <<'PY'
import json, os
status = json.loads(os.environ.get('STATUS_JSON', '{}'))
print(status.get('progress', 0))
PY
)
  printf '    attempt %02d: progress=%s\n' "$attempt" "$progress"
  if [[ "$progress" =~ ^[0-9]+$ ]] && [ "$progress" -ge 100 ]; then
    break
  fi
  sleep 1
  if [ "$attempt" -eq 30 ]; then
    echo "Status polling timed out" >&2
    exit 1
  fi
done

echo "[3/6] Fetching results summary"
RESULTS_JSON=$(curl -sS "$API_BASE/api/results/$task_id")
FAILURES_JSON=$(curl -sS "$API_BASE/api/failures/$task_id")

echo "    results count: $(python - <<'PY'
import json, os
print(len(json.loads(os.environ['RESULTS_JSON'])))
PY
)"
echo "    failures count: $(python - <<'PY'
import json, os
print(len(json.loads(os.environ['FAILURES_JSON'])))
PY
)"

echo "[4/6] Exercising retry endpoint"
python - "$API_BASE" "$task_id" <<'PY'
import json
import os
import sys
import urllib.request

base = sys.argv[1]
task_id = sys.argv[2]
req = urllib.request.Request(
    f"{base}/api/retry",
    data=json.dumps({"task_id": task_id, "token": "ABC123"}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as resp:
    payload = json.loads(resp.read().decode())
print("    retry candidates:", payload.get("candidates"))
PY

echo "[5/6] Downloading CSV exports"
curl -sS -o "$TMP_DIR/results.csv" "$API_BASE/api/download/$task_id?type=results"
curl -sS -o "$TMP_DIR/failures.csv" "$API_BASE/api/download/$task_id?type=failures"
ls -lh "$TMP_DIR"/results.csv "$TMP_DIR"/failures.csv

echo "[6/6] Optional: open frontend at $FRONTEND_BASE in a browser to trigger manual smoke test."
