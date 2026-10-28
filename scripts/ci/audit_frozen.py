"""Comprueba la política de archivos del paquete congelado y conserva un inventario."""

import ast
import json
from pathlib import Path
import re
import subprocess
import sys

from scripts.packaging_rules import omit_packaged_file


def elf_dependencies(package: Path) -> dict[str, list[str]]:
    """Registra dependencias ELF observadas; no elimina binarios por su tamaño."""
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
    """Compara los archivos congelados con la política de empaquetado y guarda evidencia."""
    toc = next(work.rglob('PYZ-00.toc'))
    entries = ast.literal_eval(toc.read_text(encoding='utf-8'))[1]
    names = {entry[0] for entry in entries}
    forbidden = ('pandas', 'pytest', '_pytest', 'pytest_cov', 'coverage',
                 'tkinterdnd2', 'rembg.cli', 'rembg.commands', 'rembg.__main__')
    included = sorted(name for name in names
                      if any(name == prefix or name.startswith(prefix + '.') for prefix in forbidden))
    files = list(package.rglob('*'))
    stale_coverage = [path.relative_to(package).as_posix() for path in files
                      if path.is_file() and (path.name.lower() == 'coverage.py'
                                             or 'coverage' in {part.lower() for part in path.parts}
                                             or (path.name.lower().startswith('coverage-')
                                                 and path.name.lower().endswith('.dist-info')))]
    video = [str(path.relative_to(package)) for path in files
             if path.name.lower().startswith('opencv_videoio_ffmpeg')]
    characters = sorted(path.name for path in files
                        if path.is_file() and path.parent.name == 'character'
                        and path.parent.parent.name == 'easyocr')
    resources = [str(path.relative_to(package)) for path in files
                 if path.is_file() and (path.suffix == '.icns' or path.name in {
                     'installer_icon.ico', 'wizard_image.bmp', 'wizard_small.bmp',
                 })]
    developer_executables = [str(path.relative_to(package)) for path in files
                             if path.is_file() and path.parent.name == 'bin'
                             and path.parent.parent.name == 'torch'
                             and omit_packaged_file(f'torch/bin/{path.name}')]
    result = {'forbidden_modules': included, 'stale_coverage_files': stale_coverage,
              'video_plugins': video,
              'ocr_characters': characters, 'unused_assets': resources,
              'python_modules': len(names), 'developer_executables': developer_executables}
    if sys.platform == 'linux':
        result['elf_needed'] = elf_dependencies(package)
        result['unexpected_system_libraries'] = [
            path for path in result['elf_needed'] if Path(path).name.startswith((
                'libgtk-3.', 'libgdk-3.', 'libGL.', 'libGLX.', 'libEGL.', 'libGLdispatch.',
                'libnss3.', 'libsmime3.', 'libssl3.',
                'libglib-', 'libgio-', 'libgobject-', 'libgmodule-',
                'libSM.', 'libICE.', 'libxkbcommon',
            ))
        ]
    if enforce and (included or stale_coverage or video or resources or developer_executables
                    or result.get('unexpected_system_libraries')
                    or characters != ['en_char.txt', 'es_char.txt']):
        raise RuntimeError(json.dumps(result, indent=2))
    return result
