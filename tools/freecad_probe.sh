#!/usr/bin/env bash
set -euo pipefail

FREECAD_BIN="${FREECAD_BIN:-/Applications/FreeCAD.app/Contents/MacOS/FreeCAD}"

if [[ ! -x "$FREECAD_BIN" ]]; then
  echo "FreeCAD binary not found or not executable: $FREECAD_BIN" >&2
  exit 1
fi

mkdir -p .freecad-runtime/home .freecad-runtime/data .freecad-runtime/temp

FREECAD_ENV=(
  env -i
  "HOME=$PWD/.freecad-runtime/home"
  "PATH=/usr/bin:/bin:/opt/homebrew/bin"
  "FREECAD_USER_HOME=$PWD/.freecad-runtime/home"
  "FREECAD_USER_DATA=$PWD/.freecad-runtime/data"
  "FREECAD_USER_TEMP=$PWD/.freecad-runtime/temp"
)

"${FREECAD_ENV[@]}" "$FREECAD_BIN" --version || true
"${FREECAD_ENV[@]}" "$FREECAD_BIN" --get-config ExeVersion || true
"${FREECAD_ENV[@]}" "$FREECAD_BIN" --help || true
"${FREECAD_ENV[@]}" "$FREECAD_BIN" --dump-config || true
