#!/usr/bin/env bash
# Start the backend and expose it through a Cloudflare quick tunnel.
# Prints the public https URL to paste into Lovable as VITE_API_URL.
# No Cloudflare account needed. The URL changes each time this script runs.
#
# Usage:  ./scripts/tunnel.sh            (from the repo root)
# Stop:   Ctrl-C  (kills both processes)
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"
PY="${PYTHON:-$(command -v python)}"
if [ -x /opt/anaconda3/envs/edtech/bin/python ] && [ -z "${PYTHON:-}" ]; then PY=/opt/anaconda3/envs/edtech/bin/python; fi

command -v cloudflared >/dev/null || { echo "cloudflared not found. Install: brew install cloudflared"; exit 1; }

LOG="$(mktemp -t tunnel)"
cleanup() { kill "${UV_PID:-}" "${CF_PID:-}" 2>/dev/null || true; rm -f "$LOG"; }
trap cleanup EXIT INT TERM

( cd backend && exec "$PY" -m uvicorn app.main:app --port "$PORT" ) &
UV_PID=$!
for _ in $(seq 1 40); do curl -sf "localhost:$PORT/health" >/dev/null && break; sleep 0.5; done
curl -sf "localhost:$PORT/health" >/dev/null || { echo "backend did not start on :$PORT"; exit 1; }

cloudflared tunnel --url "http://localhost:$PORT" --no-autoupdate >"$LOG" 2>&1 &
CF_PID=$!
URL=""
for _ in $(seq 1 60); do
  URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" | head -1 || true)"
  [ -n "$URL" ] && break
  sleep 0.5
done
[ -n "$URL" ] || { echo "tunnel did not come up; log:"; cat "$LOG"; exit 1; }

echo
echo "  Backend:   http://localhost:$PORT"
echo "  Public:    $URL"
echo "  Health:    $URL/health"
echo
echo "  In Lovable set  VITE_API_URL=$URL  and republish."
echo "  Keep this terminal open for the demo. Ctrl-C to stop."
echo
wait "$UV_PID"
