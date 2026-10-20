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
    item: dict = {'name': name, 'status': 'running'}
    result.setdefault('stages', []).append(item)
    started = time.perf_counter()
    try:
        value = action()
    except Exception:
        item['status'] = 'failed'
        print(f'[package-selftest] FAIL {name}', flush=True)
        raise
    finally:
        item['seconds'] = time.perf_counter() - started
        item['peak_rss_bytes'] = _peak_rss_bytes()
    item['status'] = 'passed'
    result.pop('current_stage', None)
    print(f'[package-selftest] PASS {name}', flush=True)
    return value


def _peak_rss_bytes() -> int:
    """OS peak resident memory, without adding a runtime dependency."""
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    'peak_working_set', 'working_set', 'quota_peak_paged', 'quota_paged',
                    'quota_peak_nonpaged', 'quota_nonpaged', 'pagefile', 'peak_pagefile',
                )
            ]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.peak_working_set
    import resource
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * (1 if sys.platform == 'darwin' else 1024)


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


def _verify_image_formats(work: Path, observations: dict | None = None) -> list[str]:
    """Exercise installed encoders/decoders, including native HEIC/AVIF codecs."""
    import hashlib
    from PIL import Image, ImageCms
    import piexif
    import pillow_heif
    from app.modules import convert, metadata, ocr

    pillow_heif.register_heif_opener()
    source = work / 'colores ñ.png'
    image = Image.new('RGBA', (128, 96), (30, 100, 200, 120))
    image.save(source)
    for fmt in convert.FORMATOS_DESTINO:
        result = convert.convertir_imagen(source, fmt, work)
        with Image.open(result['ruta_salida']) as output:
            output.load()
            if output.size != image.size and fmt != 'ICO':
                raise RuntimeError(f'Wrong dimensions after {fmt}: {output.size}')
            alpha_min, _ = output.convert('RGBA').getchannel('A').getextrema()
            if fmt in {'PNG', 'WEBP', 'TIFF', 'AVIF', 'HEIC', 'ICO'} and alpha_min == 255:
                raise RuntimeError(f'Lost transparency after {fmt}')
            if observations is not None:
                observations[fmt] = {'mode': output.mode, 'size': list(output.size),
                                     'pixel_sha256': hashlib.sha256(output.tobytes()).hexdigest()}
        # The real OCR input path decodes through Pillow then cv2, not FFmpeg.
        if ocr.preprocesar_imagen(result['ruta_salida']).size == 0:
            raise RuntimeError(f'OCR could not decode {fmt}')
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    for fmt, suffix in (('JPEG', '.jpg'), ('TIFF', '.tiff')):
        original = work / f'metadata{suffix}'
        edited = work / f'metadata-edited{suffix}'
        exif = piexif.dump({'0th': {piexif.ImageIFD.Make: b'Yagua-test'}, 'Exif': {}})
        image.convert('RGB').save(original, fmt, exif=exif, icc_profile=profile)
        with Image.open(original) as before:
            pixels = hashlib.sha256(before.tobytes()).hexdigest()
        ok, error = metadata.editar_exif(str(original), str(edited), {'Artist': 'Test'})
        if not ok:
            raise RuntimeError(error)
        with Image.open(edited) as output:
            if output.info.get('icc_profile') != profile:
                raise RuntimeError(f'{fmt}: color profile lost')
            if hashlib.sha256(output.tobytes()).hexdigest() != pixels:
                raise RuntimeError(f'{fmt}: metadata edit changed pixels')
        tags = piexif.load(str(edited))
        if tags['0th'][piexif.ImageIFD.Artist] != b'Test' or tags['0th'][piexif.ImageIFD.Make] != b'Yagua-test':
            raise RuntimeError(f'{fmt}: EXIF roundtrip failed')
    rotated = work / 'orientation.jpg'
    image.convert('RGB').save(rotated, exif=piexif.dump({'0th': {274: 6}}))
    result = convert.convertir_imagen(rotated, 'PNG', work)
    with Image.open(result['ruta_salida']) as output:
        if output.size != (96, 128):
            raise RuntimeError('EXIF orientation was not applied')
    return list(convert.FORMATOS_DESTINO)


def _verify_conversion_profiles(work: Path) -> dict[str, bool]:
    from PIL import Image, ImageCms
    from app.modules.convert import convertir_imagen

    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    preserved = {}
    for mode in ('RGB', 'RGBA'):
        source = work / f'profile-{mode}.png'
        Image.new('RGBA', (32, 24), (20, 80, 180, 120)).convert(mode).save(source, icc_profile=profile)
        for fmt in ('JPEG', 'WEBP'):
            result = convertir_imagen(source, fmt, work)
            with Image.open(result['ruta_salida']) as output:
                retained = output.info.get('icc_profile') == profile
            preserved[f'{mode}-{fmt}'] = retained
            # Only historical comparison permits the confirmed pre-existing bug.
            # Candidate and release validation must preserve every RGB profile.
            if not retained and os.environ.get('YAGUA_PACKAGE_BASELINE_ALLOW_ICC_LOSS') != '1':
                raise RuntimeError(f'{mode} -> {fmt}: conversion lost ICC profile')
    return preserved


def _redirect_probe_numba_cache(directory: Path) -> None:
    # Numba's user-provided locator ignores frozen modules without a source file.
    # Its fallback queries Windows known folders, ignoring LOCALAPPDATA. Redirect
    # that fallback only in this disposable verification process, before rembg
    # imports PyMatting and eagerly compiles its kernels.
    from types import SimpleNamespace
    from numba.core import caching

    directory.mkdir(parents=True, exist_ok=True)
    caching.AppDirs = lambda *args, **kwargs: SimpleNamespace(user_cache_dir=str(directory.resolve()))


def _update_checker_name(module) -> str:
    # The same probe also runs against older baseline source snapshots.
    return 'check_latest_update' if hasattr(module, 'check_latest_update') else 'check_latest_stable'


def _verify_ui_fonts(app) -> dict:
    from app.ui import fonts
    import tkinter.font as tkfont

    # The probe is also overlaid on baseline packages predating bundled CJK fonts.
    if not hasattr(fonts, 'CJK_FONTS'):
        return {'baseline': True}
    registered = fonts.registrar_fuentes()
    if not all(registered.values()):
        raise RuntimeError(f'Bundled UI font registration failed: {registered}')
    required = {'Inter', *fonts.LANGUAGE_FAMILIES.values()}
    missing = required - set(tkfont.families(app))
    if missing:
        raise RuntimeError(f'Bundled UI font families unavailable: {sorted(missing)}')
    return {'families': sorted(required), 'font_bytes': sum(
        resource_path(relative).stat().st_size for relative in fonts.CJK_FONTS)}


def _await_startup(app, timeout_seconds=60.0):
    deadline = time.monotonic() + timeout_seconds
    while not app.ready and time.monotonic() < deadline:
        if not app.winfo_exists():
            raise RuntimeError('Application closed during startup')
        app.update()
        time.sleep(.002)
    if not app.ready:
        raise TimeoutError('Application UI did not finish startup')
    preloader = app._startup.preloader
    if preloader and preloader.errors:
        raise RuntimeError(f'UI preload failed: {preloader.errors}')


def _verify_startup() -> None:
    import customtkinter as ctk
    from app.app import YaguaApp
    from app.ui import main_window
    from app.ui.scale import apply_ui_scale

    ctk.set_appearance_mode('dark')
    ctk.set_default_color_theme('blue')
    apply_ui_scale()
    with patch.object(main_window, _update_checker_name(main_window), return_value=None):
        app = YaguaApp()
        try:
            _await_startup(app)
            app.update_idletasks()
            _verify_ui_fonts(app)
        finally:
            app.destroy()


def _prepare_probe_stdio() -> None:
    # Instrumentation only: redirected Windows CI handles may use CP1252 even
    # in a windowed executable. EasyOCR's progress bar needs Unicode output.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, 'reconfigure', None)
        if callable(reconfigure):
            reconfigure(encoding='utf-8', errors='backslashreplace')


def run(report_path: Path) -> int:
    _prepare_probe_stdio()
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
    if mode == 'startup':
        result['offline'] = True
        try:
            if not result['frozen']:
                raise RuntimeError('Startup probe requires a frozen package')
            _deny_network()
            _stage(result, 'startup-home', _verify_startup)
            result['status'] = 'passed'
        except Exception:
            result['error'] = traceback.format_exc()
        report_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        return 0 if result['status'] == 'passed' else 1
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

            result['image_roundtrips'] = {}
            result['image_formats'] = _stage(result, 'image-formats-and-metadata',
                lambda: _verify_image_formats(work, result['image_roundtrips']))
            result['conversion_profiles'] = _stage(result, 'conversion-color-profiles',
                lambda: _verify_conversion_profiles(work))

            def verify_ocr(languages):
                batch_result = ocr.batch_procesar([str(image_path)], idiomas=languages)
                if batch_result['ok'] != 1 or batch_result['errores'] != 0:
                    raise RuntimeError(f'OCR batch failed: {batch_result}')
                text = batch_result['textos'][str(image_path)]
                compact = re.sub(r'\W', '', text.casefold())
                if 'holayagua123' not in compact or 'hellolinux456' not in compact:
                    raise RuntimeError(f'Unexpected OCR text: {text!r}')
                if ocr.get_reader(languages).device != 'cpu':
                    raise RuntimeError('EasyOCR reader is not using CPU')
                result['ocr_text'] = text
                return batch_result

            for languages in (['es'], ['en'], ['es', 'en']):
                label = '-'.join(languages)
                _stage(result, f'ocr-init-{label}', lambda: ocr.get_reader(languages))
                batch = _stage(result, f'ocr-{label}', lambda: verify_ocr(languages))

            def verify_background_removal(fallback=False):
                import hashlib
                foreground = Image.new('RGB', (256, 256), 'white')
                ImageDraw.Draw(foreground).ellipse((55, 30, 200, 230), fill=(180, 35, 45))
                foreground_path = work / 'foreground.png'
                foreground.save(foreground_path)
                # Force the default session to fail only in this opt-in verifier;
                # exercise the application's real compatibility fallback path.
                load_session = remove_bg._load_session

                def load(model):
                    if fallback and model == remove_bg.DEFAULT_MODEL:
                        raise RuntimeError('Self-test: simulate default model unavailable')
                    return load_session(model)

                with patch.object(remove_bg, '_load_session', side_effect=load):
                    removal_result = remove_bg.batch_quitar_fondo([str(foreground_path)], str(work))
                if removal_result['ok'] != 1 or removal_result['errores'] != 0:
                    raise RuntimeError(f'Background removal failed: {removal_result}')
                if bool(removal_result['used_fallback']) != fallback:
                    raise RuntimeError(f'Unexpected fallback state: {removal_result}')
                expected_model = remove_bg.FALLBACK_MODEL if fallback else remove_bg.DEFAULT_MODEL
                if removal_result['model_used'] != expected_model:
                    raise RuntimeError(f'Unexpected background model: {removal_result}')
                output = Image.open(removal_result['resultados'][0]['ruta_salida'])
                alpha_min, _ = output.getchannel('A').getextrema()
                if output.mode != 'RGBA' or output.size != foreground.size or isinstance(alpha_min, tuple) or alpha_min >= 255:
                    raise RuntimeError('Background output is not a transparent 256x256 RGBA image')
                result['background_model'] = removal_result['model_used']
                result['background_removal'] = 'passed'
                result.setdefault('background_roundtrips', {})[expected_model] = {
                    'mode': output.mode, 'size': list(output.size),
                    'pixel_sha256': hashlib.sha256(output.tobytes()).hexdigest(),
                }

            for fallback in (False, True):
                model = remove_bg.FALLBACK_MODEL if fallback else remove_bg.DEFAULT_MODEL

                def load_background_model():
                    _redirect_probe_numba_cache(Path(os.environ['NUMBA_CACHE_DIR']))
                    return remove_bg._load_session(model)

                _stage(result, f'background-init-{model}', load_background_model)
                _stage(result, f'background-{model}', lambda: verify_background_removal(fallback))

            import numba
            result['numba_threading_layer'] = numba.threading_layer()

            def verify_ui():
                from app.app import YaguaApp
                from app.ui import main_window
                from app.ui.module_registry import iter_all_modules

                setattr(main_window, _update_checker_name(main_window), lambda _: None)
                app = YaguaApp()
                _await_startup(app)
                result['ui_fonts'] = _verify_ui_fonts(app)
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
