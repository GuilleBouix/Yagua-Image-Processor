#!/usr/bin/env bash
# Se carga con un runtime congelado; no vuelve a crear el entorno de dependencias.
# Primero arma AppDir y, si se pidió, genera y valida el AppImage extraído.
if [[ -n "$APPDIR_PATH" ]]; then
  # Copia el runtime auditado y agrega los accesos de escritorio de Linux.
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
  # Conserva metadatos de bibliotecas: PyMatting los consulta en ejecución.
  # Wheel libraries may already have patched ELF layouts. Stripping them again
  # puede invalidar la alineación LOAD (por ejemplo, OpenBLAS de NumPy).
  # Conserva los binarios; primero se verifican artefactos y luego el límite de app, modelos y cachés.
  "$PYTHON_BIN" scripts/ci/check_linux_size.py "$APPDIR_PATH"
fi

if [[ "${BUILD_APPIMAGE:-0}" == "1" ]]; then
  # Extrae y verifica el artefacto antes de considerarlo listo para distribución.
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
