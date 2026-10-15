"""Assert the frozen contents follow the lean policy; preserve an inventory."""

import ast
import json
from pathlib import Path


def audit(package: Path, work: Path, enforce=True) -> dict:
    toc = next(work.rglob('PYZ-00.toc'))
    entries = ast.literal_eval(toc.read_text(encoding='utf-8'))[1]
    names = {entry[0] for entry in entries}
    forbidden = ('pandas', 'pytest', '_pytest', 'pytest_cov', 'coverage',
                 'tkinterdnd2', 'rembg.cli', 'rembg.commands', 'rembg.__main__')
    included = sorted(name for name in names
                      if any(name == prefix or name.startswith(prefix + '.') for prefix in forbidden))
    files = list(package.rglob('*'))
    video = [str(path.relative_to(package)) for path in files
             if path.name.lower().startswith('opencv_videoio_ffmpeg')]
    characters = sorted(path.name for path in files
                        if path.is_file() and path.parent.name == 'character'
                        and path.parent.parent.name == 'easyocr')
    resources = [str(path.relative_to(package)) for path in files
                 if path.is_file() and (path.suffix == '.icns' or path.name in {
                     'installer_icon.ico', 'wizard_image.bmp', 'wizard_small.bmp',
                 })]
    result = {'forbidden_modules': included, 'video_plugins': video,
              'ocr_characters': characters, 'unused_assets': resources,
              'python_modules': len(names)}
    if enforce and (included or video or resources or characters != ['en_char.txt', 'es_char.txt']):
        raise RuntimeError(json.dumps(result, indent=2))
    return result
