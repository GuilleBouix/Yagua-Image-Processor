#!/usr/bin/env bash
# Sourced by build_linux_appimage.sh after validating fresh output paths.
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

# Keep the HEIC chain on this build's Linux base rather than shipping an
# unidentified compatibility libmvec from the upstream wheel. Runtime versions stay pinned.
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
# Spawn with a disposable home before importing Tk, so font caches and
# preferences cannot touch the caller's profile.
xvfb-run -a "$PYTHON_BIN" scripts/ci/probe_package.py \
  "$DIST_DIR/Yagua/Yagua" "$BUILD_DIR/preflight-probe" --preflight
preflight_report="${PREFLIGHT_REPORT:-$DIST_DIR/selftest-preflight.json}"
mkdir -p "$(dirname "$preflight_report")"
cp "$BUILD_DIR/preflight-probe/preflight/selftest.json" "$preflight_report"

fi
