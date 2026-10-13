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
BUILD_STAMP="$(date +%Y%m%d-%H%M%S)"
DIST_DIR="$(realpath -m "${DIST_DIR:-$ROOT_DIR/dist/local-linux-$BUILD_STAMP}")"
BUILD_DIR="$(realpath -m "${BUILD_DIR:-$ROOT_DIR/build/local-linux-$BUILD_STAMP}")"
APPDIR_PATH="${TARGET_APPDIR:-${APPDIR_PATH:-}}"

if [[ -z "$APPDIR_PATH" && "${BUILD_APPIMAGE:-0}" == "1" ]]; then
  APPDIR_PATH="$BUILD_DIR/AppDir"
fi

for output in "$BUILD_DIR" "$DIST_DIR/Yagua"; do
  if [[ -e "$output" ]]; then
    echo "El destino ya existe; usa carpetas nuevas: $output" >&2
    exit 1
  fi
done
if [[ -n "$APPDIR_PATH" && -e "$APPDIR_PATH" ]]; then
  echo "AppDir ya existe; usa una carpeta nueva: $APPDIR_PATH" >&2
  exit 1
fi
"$PYTHON_BIN" - <<'PY'
import importlib.metadata
import torch
import torchvision

assert torch.__version__ == '2.11.0+cpu', 'Instala requirements-linux-cpu.txt'
assert torchvision.__version__ == '0.26.0+cpu'
assert torch.version.cuda is None
assert not any(d.metadata['Name'].lower().startswith('nvidia-')
               for d in importlib.metadata.distributions()), 'El entorno incluye NVIDIA'
PY

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  "$SPEC_FILE"

"$PYTHON_BIN" scripts/ci/check_linux_size.py "$DIST_DIR/Yagua"

if [[ -n "$APPDIR_PATH" ]]; then
  mkdir -p \
    "$APPDIR_PATH/usr/lib/yagua" \
    "$APPDIR_PATH/usr/share/applications" \
    "$APPDIR_PATH/usr/share/icons/hicolor/256x256/apps"

  cp -a "$DIST_DIR/Yagua/." "$APPDIR_PATH/usr/lib/yagua/"
  cp "$ROOT_DIR/packaging/linux/yagua.desktop" "$APPDIR_PATH/usr/share/applications/yagua.desktop"
  cp "$ROOT_DIR/assets/icon.png" "$APPDIR_PATH/usr/share/icons/hicolor/256x256/apps/yagua.png"

  find "$APPDIR_PATH" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
  find "$APPDIR_PATH" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
  find "$APPDIR_PATH/usr/lib/yagua" -type d \( -name "tests" -o -name "test" \) -prune -exec rm -rf {} + 2>/dev/null || true
  # Keep library metadata: PyMatting queries it at runtime.
  find "$APPDIR_PATH/usr/lib/yagua" -type f -name "*.so*" -exec strip --strip-unneeded {} + 2>/dev/null || true
  strip --strip-unneeded "$APPDIR_PATH/usr/lib/yagua/Yagua" 2>/dev/null || true
  "$PYTHON_BIN" scripts/ci/check_linux_size.py "$APPDIR_PATH"
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
  APPDIR_PATH="$(realpath "$APPDIR_PATH")"
  export APP_VERSION APPDIR_PATH
  appimage="$DIST_DIR/Yagua-$APP_VERSION-x86_64.AppImage"
  if [[ -e "$appimage" ]]; then
    echo "El AppImage de destino ya existe: $appimage" >&2
    exit 1
  fi
  (
    cd "$DIST_DIR"
    appimage-builder --recipe "$ROOT_DIR/packaging/linux/AppImageBuilder.yml" \
      --appdir "$APPDIR_PATH" --build-dir "$BUILD_DIR/appimage-builder"
  )
  mkdir "$BUILD_DIR/package-check"
  (
    cd "$BUILD_DIR/package-check"
    "$appimage" --appimage-extract > extract.log
  )
  "$PYTHON_BIN" scripts/ci/check_linux_size.py "$DIST_DIR/Yagua" "$appimage" \
    "$BUILD_DIR/package-check/squashfs-root" --report "$DIST_DIR/sizes.json"
  (
    cd "$DIST_DIR"
    sha256sum "$(basename "$appimage")" > "$(basename "$appimage").sha256"
  )
fi

echo "Build Linux listo en $DIST_DIR/Yagua"
