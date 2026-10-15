"""Assert the frozen contents follow the lean policy; preserve an inventory."""

import ast
import json
from pathlib import Path
import re
import subprocess
import sys


def elf_dependencies(package: Path) -> dict[str, list[str]]:
    """Record actual ELF dependencies, never remove binaries by their size."""
    needed = {}
    for path in package.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                continue
        result = subprocess.run(['readelf', '-d', str(path)], capture_output=True,
                                text=True, check=True)
        needed[str(path.relative_to(package))] = re.findall(
            r'\(NEEDED\).*?\[([^\]]+)\]', result.stdout,
        )
    return needed


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
    if sys.platform == 'linux':
        result['elf_needed'] = elf_dependencies(package)
    if enforce and (included or video or resources or characters != ['en_char.txt', 'es_char.txt']):
        raise RuntimeError(json.dumps(result, indent=2))
    return result
