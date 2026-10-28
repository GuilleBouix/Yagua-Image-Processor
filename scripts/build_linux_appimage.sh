#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Los modos runtime, AppImage y completo comparten los pasos aislados de build.
BUILD_PHASE="${BUILD_PHASE:-all}"
if [[ "$BUILD_PHASE" != "all" && "$BUILD_PHASE" != "runtime" && "$BUILD_PHASE" != "appimage" ]]; then
  echo "Unknown build phase: $BUILD_PHASE" >&2
  exit 1
fi

# Si se indica un intérprete, se usa ese. Si no, crea un entorno nuevo de build;
# nunca instala en .venv del editor ni en el entorno de pruebas.
if [[ -z "${PYTHON_BIN:-}" && "$BUILD_PHASE" != "appimage" ]]; then
  environment_root="$(mktemp -d -t yagua-build-XXXXXXXX)"
  python3 -m venv "$environment_root/venv"
  PYTHON_BIN="$environment_root/venv/bin/python"
  "$PYTHON_BIN" -m pip install -r requirements-linux-cpu.txt -r requirements-build.txt
fi

SPEC_FILE="${SPEC_FILE:-Yagua.linux.spec}"
# Usa destinos nuevos para no confundir artefactos antiguos con esta compilación.
BUILD_STAMP="$(date +%Y%m%d-%H%M%S)"
DIST_DIR="$(realpath -m "${DIST_DIR:-$ROOT_DIR/dist/local-linux-$BUILD_STAMP}")"
BUILD_DIR="$(realpath -m "${BUILD_DIR:-$ROOT_DIR/build/local-linux-$BUILD_STAMP}")"
APPDIR_PATH="${TARGET_APPDIR:-${APPDIR_PATH:-}}"

if [[ -z "$APPDIR_PATH" && "${BUILD_APPIMAGE:-0}" == "1" ]]; then
  APPDIR_PATH="$BUILD_DIR/AppDir"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ "$BUILD_PHASE" != "appimage" ]]; then
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
  source "$ROOT_DIR/scripts/build_linux_runtime.sh"
fi
if [[ "$BUILD_PHASE" != "runtime" ]]; then
  source "$ROOT_DIR/scripts/package_linux_appimage.sh"
fi
