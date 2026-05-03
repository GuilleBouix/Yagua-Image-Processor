#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/venv/bin/python"
fi

SPEC_FILE="${SPEC_FILE:-Yagua.linux.spec}"
DIST_DIR="${DIST_DIR:-$ROOT_DIR/dist}"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build/linux}"
APPDIR_PATH="${TARGET_APPDIR:-${APPDIR_PATH:-}}"

if [[ -z "$APPDIR_PATH" && "${BUILD_APPIMAGE:-0}" == "1" ]]; then
  APPDIR_PATH="$ROOT_DIR/AppDir"
fi

rm -rf "$BUILD_DIR" "$DIST_DIR/Yagua"

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  "$SPEC_FILE"

if [[ -n "$APPDIR_PATH" ]]; then
  rm -rf "$APPDIR_PATH"
  mkdir -p \
    "$APPDIR_PATH/usr/bin" \
    "$APPDIR_PATH/usr/lib/yagua" \
    "$APPDIR_PATH/usr/share/applications" \
    "$APPDIR_PATH/usr/share/icons/hicolor/256x256/apps"

  cp -a "$DIST_DIR/Yagua/." "$APPDIR_PATH/usr/lib/yagua/"
  cp "$ROOT_DIR/packaging/linux/yagua.desktop" "$APPDIR_PATH/usr/share/applications/yagua.desktop"
  cp "$ROOT_DIR/assets/icon.png" "$APPDIR_PATH/usr/share/icons/hicolor/256x256/apps/yagua.png"

  cat > "$APPDIR_PATH/usr/bin/yagua" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPDIR="$(cd "$SELF_DIR/../.." && pwd)"
exec "$APPDIR/usr/lib/yagua/Yagua" "$@"
EOF
  chmod +x "$APPDIR_PATH/usr/bin/yagua"
fi

if [[ "${BUILD_APPIMAGE:-0}" == "1" ]]; then
  if ! command -v appimage-builder >/dev/null 2>&1; then
    echo "appimage-builder no esta instalado en PATH" >&2
    exit 1
  fi
  APP_VERSION="${APP_VERSION:-$("$PYTHON_BIN" - <<'PY'
from app.version import __version__
print(__version__)
PY
)}"
  export APP_VERSION
  appimage-builder --recipe "$ROOT_DIR/packaging/linux/AppImageBuilder.yml"
fi

echo "Build Linux listo en $DIST_DIR/Yagua"
