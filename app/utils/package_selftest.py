"""Opt-in Linux package verification; normal application startup never calls this."""

from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import re
import socket
import sys
import traceback
from unittest.mock import patch


def run(report_path: Path) -> int:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    result: dict = {'status': 'failed', 'frozen': bool(getattr(sys, 'frozen', False))}
    offline = os.environ.get('YAGUA_PACKAGE_OFFLINE') == '1'
    result['offline'] = offline
    try:
        if not result['frozen']:
            raise RuntimeError('This verification must run inside the frozen Linux package.')
        if offline:
            def deny_network(*args, **kwargs):
                raise RuntimeError('Network access forbidden during offline verification')

            socket.socket.connect = deny_network
            socket.create_connection = deny_network

        import torch
        import torchvision
        from PIL import Image, ImageDraw, ImageFont
        from app.modules import ocr, remove_bg

        assert torch.__version__ == '2.11.0+cpu', torch.__version__
        assert torchvision.__version__ == '0.26.0+cpu', torchvision.__version__
        assert torch.version.cuda is None
        torch.set_num_threads(2)
        result['torch'] = torch.__version__
        result['torchvision'] = torchvision.__version__
        result['pymatting'] = importlib.metadata.version('pymatting')

        work = report_path.parent / report_path.stem
        work.mkdir()
        image_path = work / 'ocr-sample.png'
        sample = Image.new('RGB', (1000, 260), 'white')
        draw = ImageDraw.Draw(sample)
        font = ImageFont.truetype('DejaVuSans.ttf', 52)
        draw.text((30, 30), 'Hola Yagua 123', fill='black', font=font)
        draw.text((30, 135), 'Hello Linux 456', fill='black', font=font)
        sample.save(image_path)
        batch = ocr.batch_procesar([str(image_path)], idiomas=['es', 'en'])
        assert batch['ok'] == 1 and batch['errores'] == 0, batch
        text = batch['textos'][str(image_path)]
        compact = re.sub(r'\W', '', text.casefold())
        assert 'holayagua123' in compact and 'hellolinux456' in compact, text
        assert ocr.get_reader(['es', 'en']).device == 'cpu'
        result['ocr_text'] = text

        foreground = Image.new('RGB', (256, 256), 'white')
        ImageDraw.Draw(foreground).ellipse((55, 30, 200, 230), fill=(180, 35, 45))
        foreground_path = work / 'foreground.png'
        foreground.save(foreground_path)
        removal = remove_bg.batch_quitar_fondo([str(foreground_path)], str(work))
        assert removal['ok'] == 1 and removal['errores'] == 0, removal
        assert removal['used_fallback'] is False, removal
        output = Image.open(removal['resultados'][0]['ruta_salida'])
        assert output.mode == 'RGBA' and output.size == foreground.size
        alpha_min, _ = output.getchannel('A').getextrema()
        assert isinstance(alpha_min, (int, float)) and alpha_min < 255
        result['background_model'] = removal['model_used']
        result['background_removal'] = 'passed'

        from app.app import YaguaApp
        from app.ui import main_window
        from app.ui.module_registry import iter_all_modules

        # Startup updates are unrelated to OCR and would contact GitHub in the offline pass.
        main_window.check_latest_stable = lambda _: None
        app = YaguaApp()
        callback_errors: list[str] = []
        app.report_callback_exception = lambda kind, value, tb: callback_errors.append(str(value))

        def verify_ui():
            try:
                keys = [spec.key for spec in iter_all_modules() if spec.enabled]
                for key in keys:
                    app.main_window.show_module(key)
                    app.update_idletasks()
                app.main_window.show_module('ocr')
                frame = app.main_window.frames['ocr']
                frame._finalizar_ocr(batch)
                frame._copiar_texto()
                expected = frame._textarea.get('0.0', 'end').strip()
                assert app.clipboard_get() == expected
                with patch('app.ui.frames.ocr.frame.filedialog.askdirectory',
                           return_value=str(work)):
                    frame._exportar()
                exports = list(work.glob('texto_extraido*.txt'))
                assert len(exports) == 1 and exports[0].read_text(encoding='utf-8') == expected
                result['modules_loaded'] = keys
                result['clipboard'] = 'passed'
                result['txt_export'] = 'passed'
                app.after(1500, finish)
            except Exception:
                result['error'] = traceback.format_exc()
                app.destroy()

        def finish():
            if callback_errors:
                result['error'] = '\n'.join(callback_errors)
            else:
                result['status'] = 'passed'
            app.destroy()

        app.after(0, verify_ui)
        app.mainloop()
    except Exception:
        result['error'] = traceback.format_exc()
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n',
                           encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'passed' else 1
