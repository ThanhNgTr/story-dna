#!/usr/bin/env bash
# Start the story-dna web app on http://127.0.0.1:8765 (local only).
set -euo pipefail
cd "$(dirname "$0")"
# Local secrets / settings (HF_TOKEN, CLAUDE_BIN, STORY_DNA_PARALLEL, ...). .env is gitignored.
if [ -f .env ]; then
  set -a; . ./.env; set +a
fi
if [ ! -x .venv/bin/python ]; then
  echo "Missing .venv: run ./install.sh first." >&2; exit 1
fi
.venv/bin/python -c "import fastapi, uvicorn" 2>/dev/null || \
  ~/.local/bin/uv pip install --python .venv/bin/python -r app/requirements.txt
[ -f app/static/ui/index.html ] || echo "Note: new UI not built (cd web && npm install && npm run build). Old UI still works." >&2
echo "story-dna: http://127.0.0.1:${PORT:-8765}/ui/  (old UI: http://127.0.0.1:${PORT:-8765}/)"
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8765}"
