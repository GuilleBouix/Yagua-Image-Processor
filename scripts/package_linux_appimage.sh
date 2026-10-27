#!/usr/bin/env bash
# Sourced with an existing frozen runtime; no dependency environment is rebuilt.
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
  # Wheel libraries may already have patched ELF layouts. Stripping them again
  # can invalidate LOAD segment alignment (for example NumPy's OpenBLAS).
  # Keep the binaries intact; the artifact checks precede the final app + models + cache budget check.
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
  test -x "$appimage"
  mkdir "$BUILD_DIR/package-check"
  (
    cd "$BUILD_DIR/package-check"
    "$appimage" --appimage-extract > extract.log
  )
  "$PYTHON_BIN" scripts/ci/check_linux_size.py "$DIST_DIR/Yagua" "$appimage" \
    "$BUILD_DIR/package-check/squashfs-root" --report "$DIST_DIR/sizes.json"
  test -x "$BUILD_DIR/package-check/squashfs-root/AppRun"
  test -x "$BUILD_DIR/package-check/squashfs-root/usr/lib/yagua/Yagua"
  (
    cd "$DIST_DIR"
    sha256sum "$(basename "$appimage")" > "$(basename "$appimage").sha256"
  )
fi

echo "Build Linux listo en $DIST_DIR/Yagua"
