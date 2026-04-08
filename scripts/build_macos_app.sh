#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/venv/bin/python"
fi

"$PYTHON_BIN" -m pip install pyinstaller

"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --specpath "$ROOT_DIR/build" \
  --distpath "$ROOT_DIR/dist" \
  --name "Yagua" \
  --icon "$ROOT_DIR/assets/icon.icns" \
  --add-data "$ROOT_DIR/assets:assets" \
  --collect-data "customtkinter" \
  --collect-all "rembg" \
  --collect-all "pymatting" \
  --collect-submodules "app.ui.frames" \
  --collect-submodules "app.translations" \
  --osx-bundle-identifier "com.yagua.imageprocessor" \
  "main.py"

echo "Build listo: $ROOT_DIR/dist/Yagua.app"
