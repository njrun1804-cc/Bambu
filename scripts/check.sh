#!/usr/bin/env bash
set -euo pipefail

echo "intentional shared-CI failure canary" >&2
exit 97

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${CHECK_RUNNER_ACTIVE:-0}" != "1" ]]; then
  CHECK_RUN_CACHE_ALLOWED=0 exec "$script_dir/check-runner.sh" "$script_dir/check.sh" "$@"
fi
cd "$(dirname "$0")/.."

uv run ruff check bambu tools tests
uv run ruff format --check bambu tools tests
uv run python - <<'PY'
import unittest

suite = unittest.defaultTestLoader.discover("tests")
if suite.countTestCases() == 0:
    raise SystemExit("No unittest tests collected")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
PY
