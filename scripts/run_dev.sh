#!/usr/bin/env bash
# Mini README:
# Linux/macOS/RPi helper script for local development startup.
set -euo pipefail
PORT="${1:-8000}"
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
