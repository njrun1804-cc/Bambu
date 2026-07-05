#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

uv run ruff check bambu tools tests
uv run ruff format --check bambu tools tests
uv run python -m unittest discover -s tests
