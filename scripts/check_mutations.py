"""Inyecta regresiones en copias descartables sin modificar el checkout."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('partial-write', 'app/utils/output.py', 'temporary = Path(name)', 'temporary = target', 'tests/test_write_safety.py::test_partial_write_preserves_original'),
    ('jpeg-recompression', 'app/modules/metadata.py', "if formato == 'JPEG' and request.orientation is None:", 'if False:', 'tests/test_write_safety.py::test_jpeg_metadata_keeps_pixels_and_profile'),
    ('multipage-loss', 'app/utils/output.py', "if getattr(image, 'n_frames', 1) != 1 or getattr(image, 'is_animated', False):", 'if False:', 'tests/test_write_safety.py::test_multipage_edit_rejected_without_changes'),
    ('iso-overflow', 'app/modules/metadata.py', 'not 0 <= numero <= 65535', 'not 0 <= numero <= 65536', 'tests/test_write_safety.py::test_iso_encoding_boundary'),
    ('exif-privacy', 'app/modules/compress.py', 'if tam_comprimido >= tam_original and not quitar_exif:', 'if tam_comprimido >= tam_original:', 'tests/test_write_safety.py::test_compression_strips_exif_even_if_larger'),
    ('double-start', 'app/ui/operations.py', 'if self._active is not None:', 'if False:', 'tests/ui/test_operations.py::test_coordinator_allows_only_one_global_operation'),
    ('stale-completion', 'app/ui/operations.py', 'self._active is None or self._active.id != operation_id', 'self._active is None', 'tests/ui/test_operations.py::test_stale_completion_cannot_release_new_operation'),
    ('destroyed-widget', 'app/ui/operations.py', 'if widget_exists(owner):', 'if True:', 'tests/ui/test_operations.py::test_destroyed_owner_receives_no_callbacks'),
    ('busy-controls', 'app/ui/frames/base.py', "widget.configure(state='disabled')", 'pass', 'tests/ui/test_operations.py::test_each_module_restores_real_controls_after_job'),
    ('wrong-editor-target', 'app/ui/frames/metadata/frame.py', 'ruta = self._state.ruta_edicion', 'ruta = self._state.ruta', 'tests/ui/test_metadata_frame.py::test_view_selection_does_not_redirect_editor_save'),
    ('output-collision', 'app/utils/output.py', 'if replace:', 'if True:', 'tests/test_write_safety.py::test_publish_does_not_overwrite_competing_output'),
]


def main():
    """Prepara copias descartables, inyecta fallos conocidos y comprueba si las pruebas los detectan."""
    reports = []
    for name, relative, before, after, test in CASES:
        with TemporaryDirectory(prefix='yagua-mutation-') as directory:
            work = Path(directory)
            for folder in ('app', 'tests', 'scripts'):
                shutil.copytree(ROOT / folder, work / folder, ignore=shutil.ignore_patterns('__pycache__'))
            path = work / relative
            source = path.read_text(encoding='utf-8')
            if before not in source:
                raise RuntimeError(f'Mutation anchor missing: {name}')
            path.write_text(source.replace(before, after, 1), encoding='utf-8')
            result = subprocess.run([sys.executable, 'scripts/verify.py', '-q', test, '--tb=short'], cwd=work, capture_output=True, text=True)
            detected = result.returncode == 1 and 'failed' in result.stdout
            reports.append({'mutation': name, 'test': test, 'detected': detected, 'output': result.stdout[-2500:]})
            print(name, 'DETECTED' if detected else 'NOT DETECTED', flush=True)
    target = ROOT / 'audit' / 'mutation-results.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding='utf-8')
    return 0 if all(row['detected'] for row in reports) else 1


if __name__ == '__main__':
    raise SystemExit(main())
