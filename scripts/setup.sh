#!/usr/bin/env bash
# One-command dev setup: pinned FalkorDB, install, smoke test.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install it, then re-run scripts/setup.sh" >&2
  exit 1
fi

docker compose up -d --wait

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/test_smoke.py
