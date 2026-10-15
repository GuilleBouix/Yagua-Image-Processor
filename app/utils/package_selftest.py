"""Opt-in Linux package verification; normal application startup never calls this."""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import socket
import sys
import time
import traceback
from unittest.mock import patch

from app.utils.paths import resource_path


def _load_inter_font(size: int = 52):
    from PIL import ImageFont

    font_path = resource_path('assets/fonts/Inter.ttf')
    if not font_path.is_file():
        raise RuntimeError(f'Packaged Inter font is missing: {font_path}')
    try:
        return ImageFont.truetype(str(font_path), size)
    except OSError as exc:
        raise RuntimeError(f'Packaged Inter font cannot be opened: {font_path}') from exc


def _wait_for_ui(app, ready, on_ready, on_timeout, timeout_seconds=30.0, clock=time.monotonic):
    """Poll asynchronous frame initialization without blocking Tk's event loop."""
    deadline = clock() + timeout_seconds

    def poll():
        if ready():
            on_ready()
        elif clock() >= deadline:
            on_timeout()
        else:
            app.after(100, poll)

    app.after(0, poll)


def _stage(result: dict, name: str, action):
    print(f'[package-selftest] START {name}', flush=True)
    result['current_stage'] = name
    item = {'name': name, 'status': 'running'}
    result.setdefault('stages', []).append(item)
    try:
        value = action()
    except Exception:
        item['status'] = 'failed'
        print(f'[package-selftest] FAIL {name}', flush=True)
        raise
    item['status'] = 'passed'
    result.pop('current_stage', None)
    print(f'[package-selftest] PASS {name}', flush=True)
    return value


def _deny_network() -> None:
    def denied(*args, **kwargs):
        raise RuntimeError('Network access forbidden during offline verification')

    socket.socket.connect = denied
    socket.create_connection = denied


def _verify_runtime(result: dict):
    modules = {
        name: importlib.import_module(name)
        for name in ('numpy', 'scipy', 'cv2', 'onnxruntime', 'torch', 'torchvision')
    }
    torch = modules['torch']
    torchvision = modules['torchvision']
    if sys.platform == 'linux' and torch.__version__ != '2.11.0+cpu':
        raise RuntimeError(f'Unexpected torch build: {torch.__version__}')
    if sys.platform == 'linux' and torchvision.__version__ != '0.26.0+cpu':
        raise RuntimeError(f'Unexpected torchvision build: {torchvision.__version__}')
    if sys.platform == 'linux' and torch.version.cuda is not None:
        raise RuntimeError(f'CUDA-enabled torch was packaged: {torch.version.cuda}')
    distributions = [str(dist.metadata.get('Name') or '').lower()
                     for dist in importlib.metadata.distributions()]
    nvidia = sorted(name for name in distributions if name.startswith('nvidia-'))
    if sys.platform == 'linux' and nvidia:
        raise RuntimeError(f'NVIDIA packages were bundled: {nvidia}')
    torch.set_num_threads(2)
    result.update({
        'torch': torch.__version__,
        'torchvision': torchvision.__version__,
        'numpy': modules['numpy'].__version__,
        'scipy': modules['scipy'].__version__,
        'opencv': modules['cv2'].__version__,
        'onnxruntime': modules['onnxruntime'].__version__,
        'onnxruntime_providers': modules['onnxruntime'].get_available_providers(),
        'pymatting': importlib.metadata.version('pymatting'),
        'nvidia_packages': nvidia,
    })
    return modules


def _verify_restart_target(result: dict) -> None:
    from app.ui.frames.settings.services import _restart_command

    command = _restart_command()
    target = Path(command[0])
    if not target.is_file():
        raise RuntimeError(f'Restart target does not exist: {target}')
    if os.name != 'nt' and not os.access(target, os.X_OK):
        raise RuntimeError(f'Restart target is not executable: {target}')
    appimage = os.environ.get('APPIMAGE')
    if appimage and target.resolve() != Path(appimage).resolve():
        raise RuntimeError(f'Restart target is not the running AppImage: {target}')
    result['restart_target'] = str(target)
    result['restart_uses_appimage'] = bool(appimage)


def _render_ocr_sample(work: Path):
    from PIL import Image, ImageDraw

    image_path = work / 'ocr-sample.png'
    sample = Image.new('RGB', (1000, 260), 'white')
    draw = ImageDraw.Draw(sample)
    font = _load_inter_font(52)
    draw.text((30, 30), 'Hola Yagua 123', fill='black', font=font)
    draw.text((30, 135), 'Hello Linux 456', fill='black', font=font)
    sample.save(image_path)
    return image_path


def run(report_path: Path) -> int:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    mode = os.environ.get('YAGUA_PACKAGE_SELFTEST_MODE', 'full')
    offline = os.environ.get('YAGUA_PACKAGE_OFFLINE') == '1'
    result: dict = {
        'status': 'failed',
        'frozen': bool(getattr(sys, 'frozen', False)),
        'mode': mode,
        'offline': offline,
        'stages': [],
    }
    try:
        if mode not in {'preflight', 'full'}:
            raise RuntimeError(f'Unknown package self-test mode: {mode}')
        if not result['frozen']:
            raise RuntimeError('This verification must run inside the frozen package.')
        if offline:
            _deny_network()

        _stage(result, 'native-imports-and-cpu', lambda: _verify_runtime(result))
        _stage(result, 'restart-target', lambda: _verify_restart_target(result))
        work = report_path.parent / report_path.stem
        work.mkdir()
        image_path = _stage(result, 'packaged-font-and-render',
                            lambda: _render_ocr_sample(work))

        if mode == 'preflight':
            result['status'] = 'passed'
        else:
            from PIL import Image, ImageDraw
            from app.modules import ocr, remove_bg

            def verify_ocr():
                batch_result = ocr.batch_procesar([str(image_path)], idiomas=['es', 'en'])
                if batch_result['ok'] != 1 or batch_result['errores'] != 0:
                    raise RuntimeError(f'OCR batch failed: {batch_result}')
                text = batch_result['textos'][str(image_path)]
                compact = re.sub(r'\W', '', text.casefold())
                if 'holayagua123' not in compact or 'hellolinux456' not in compact:
                    raise RuntimeError(f'Unexpected OCR text: {text!r}')
                if ocr.get_reader(['es', 'en']).device != 'cpu':
                    raise RuntimeError('EasyOCR reader is not using CPU')
                result['ocr_text'] = text
                return batch_result

            batch = _stage(result, 'ocr-es-en', verify_ocr)

            def verify_background_removal():
                foreground = Image.new('RGB', (256, 256), 'white')
                ImageDraw.Draw(foreground).ellipse((55, 30, 200, 230), fill=(180, 35, 45))
                foreground_path = work / 'foreground.png'
                foreground.save(foreground_path)
                removal_result = remove_bg.batch_quitar_fondo([str(foreground_path)], str(work))
                if removal_result['ok'] != 1 or removal_result['errores'] != 0:
                    raise RuntimeError(f'Background removal failed: {removal_result}')
                if removal_result['used_fallback']:
                    raise RuntimeError(f'Background model fallback used: {removal_result}')
                if removal_result['model_used'] != remove_bg.DEFAULT_MODEL:
                    raise RuntimeError(f'Unexpected background model: {removal_result}')
                output = Image.open(removal_result['resultados'][0]['ruta_salida'])
                alpha_min, _ = output.getchannel('A').getextrema()
                if output.mode != 'RGBA' or output.size != foreground.size or isinstance(alpha_min, tuple) or alpha_min >= 255:
                    raise RuntimeError('Background output is not a transparent 256x256 RGBA image')
                result['background_model'] = removal_result['model_used']
                result['background_removal'] = 'passed'

            _stage(result, 'background-removal', verify_background_removal)

            def verify_ui():
                from app.app import YaguaApp
                from app.ui import main_window
                from app.ui.module_registry import iter_all_modules

                main_window.check_latest_stable = lambda _: None
                app = YaguaApp()
                callback_errors: list[str] = []

                def callback_error(kind, value, tb):
                    callback_errors.append(''.join(traceback.format_exception(kind, value, tb)))

                app.report_callback_exception = callback_error
                keys = [spec.key for spec in iter_all_modules() if spec.enabled]

                def create_frames():
                    try:
                        for key in keys:
                            app.main_window.show_module(key)
                            app.update_idletasks()
                    except Exception:
                        result['ui_error'] = traceback.format_exc()
                        app.destroy()
                        return

                    def ready():
                        ocr_frame = app.main_window.frames.get('ocr')
                        remove_frame = app.main_window.frames.get('remove_bg')
                        return (
                            not callback_errors
                            and ocr_frame is not None
                            and getattr(ocr_frame, '_ocr_ready', False)
                            and remove_frame is not None
                            and hasattr(remove_frame, '_btn_seleccionar')
                        )

                    def finish_checks():
                        try:
                            app.main_window.show_module('ocr')
                            frame = app.main_window.frames['ocr']
                            frame._finalizar_ocr(batch)
                            frame._copiar_texto()
                            expected = frame._textarea.get('0.0', 'end').strip()
                            if app.clipboard_get() != expected:
                                raise RuntimeError('Clipboard content does not match OCR text')
                            with patch('app.ui.frames.ocr.frame.filedialog.askdirectory',
                                       return_value=str(work)):
                                frame._exportar()
                            exports = list(work.glob('texto_extraido*.txt'))
                            if len(exports) != 1 or exports[0].read_text(encoding='utf-8') != expected:
                                raise RuntimeError('TXT export does not match OCR text')
                            result['modules_loaded'] = keys
                            result['clipboard'] = 'passed'
                            result['txt_export'] = 'passed'
                            result['ui_status'] = 'passed'
                        except Exception:
                            result['ui_error'] = traceback.format_exc()
                        finally:
                            app.destroy()

                    def timeout():
                        details = '\n'.join(callback_errors) if callback_errors else 'frames not ready'
                        result['ui_error'] = f'UI initialization timed out after 30 seconds: {details}'
                        app.destroy()

                    _wait_for_ui(app, ready, finish_checks, timeout)

                app.after(0, create_frames)
                app.mainloop()
                if callback_errors:
                    raise RuntimeError('\n'.join(callback_errors))
                if result.get('ui_status') != 'passed':
                    raise RuntimeError(result.get('ui_error', 'UI verification did not finish'))

            _stage(result, 'ui-navigation-clipboard-export', verify_ui)
            result['status'] = 'passed'
    except Exception:
        result['error'] = traceback.format_exc()
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n',
                           encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result['status'] == 'passed' else 1
