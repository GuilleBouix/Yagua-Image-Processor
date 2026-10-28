#!/usr/bin/env bash
# Se carga desde build_linux_appimage.sh después de validar destinos nuevos.
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

# Compila la cadena HEIC sobre la base Linux de este build, en lugar de incluir una
# libmvec de compatibilidad sin identificar del wheel upstream. Las versiones siguen fijadas.
HEIC_BUILD_DIR="${HEIC_BUILD_DIR:-$ROOT_DIR/build/heic-source-$BUILD_STAMP}"
export YAGUA_HEIC_NATIVE_REPORT="${YAGUA_HEIC_NATIVE_REPORT:-$DIST_DIR/linux-heic-native.json}"
"$PYTHON_BIN" scripts/ci/build_heic_linux.py --work-dir "$HEIC_BUILD_DIR" \
  --report "$YAGUA_HEIC_NATIVE_REPORT" --jobs "${HEIC_BUILD_JOBS:-2}"

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  "$SPEC_FILE"

"$PYTHON_BIN" scripts/ci/check_linux_size.py "$DIST_DIR/Yagua"
"$PYTHON_BIN" scripts/ci/build_heic_linux.py --check-package "$DIST_DIR/Yagua"
"$PYTHON_BIN" scripts/ci/check_licenses.py --package "$DIST_DIR/Yagua" --platform linux \
  --report "$DIST_DIR/licenses.json"
test -x "$DIST_DIR/Yagua/Yagua"
if [[ "$BUILD_PHASE" == "all" ]]; then
# Usa un HOME temporal antes de importar Tk para que la caché de fuentes y
# las preferencias no modifiquen el perfil de quien ejecuta la prueba.
xvfb-run -a "$PYTHON_BIN" scripts/ci/probe_package.py \
  "$DIST_DIR/Yagua/Yagua" "$BUILD_DIR/preflight-probe" --preflight
preflight_report="${PREFLIGHT_REPORT:-$DIST_DIR/selftest-preflight.json}"
mkdir -p "$(dirname "$preflight_report")"
cp "$BUILD_DIR/preflight-probe/preflight/selftest.json" "$preflight_report"

fi
