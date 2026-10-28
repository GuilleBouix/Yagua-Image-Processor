"""Build the pinned HEIC libraries locally; do not download or replace dependencies globally."""
# Compila dependencias HEIC fijadas en un entorno Linux descartable.
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[2]
VERSIONS = {'libheif': '1.21.2', 'libde265': '1.0.16', 'x265': '4.1+1-1d117be'}
HEIF_FLAGS = [
    '-DBUILD_TESTING=OFF', '-DENABLE_PLUGIN_LOADING=OFF',
    '-DWITH_EXAMPLES=OFF', '-DWITH_EXAMPLE_HEIF_VIEW=OFF', '-DWITH_GDK_PIXBUF=OFF',
    '-DWITH_LIBDE265=ON', '-DWITH_LIBDE265_PLUGIN=OFF',
    '-DWITH_X265=ON', '-DWITH_X265_PLUGIN=OFF', '-DWITH_HEADER_COMPRESSION=OFF',
    '-DWITH_LIBSHARPYUV=OFF',
] + [f'-DWITH_{name}=OFF' for name in [
    'AOM_DECODER', 'AOM_DECODER_PLUGIN', 'AOM_ENCODER', 'AOM_ENCODER_PLUGIN',
    'RAV1E', 'RAV1E_PLUGIN', 'DAV1D', 'DAV1D_PLUGIN', 'SvtEnc', 'SvtEnc_PLUGIN',
    'KVAZAAR', 'KVAZAAR_PLUGIN', 'JPEG_DECODER', 'JPEG_ENCODER',
    'OpenJPEG_DECODER', 'OpenJPEG_ENCODER', 'OPENJPH_DECODER', 'OPENJPH_ENCODER',
    'OpenH264_DECODER', 'OpenH264_ENCODER',
]]


def digest(path: Path) -> str:
    """Calcula el SHA-256 usado para identificar fuentes y binarios."""
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def extract_sources(work: Path, root: Path = ROOT) -> tuple[dict, dict]:
    """Verifica y extrae las fuentes fijadas para la compilación local de HEIC."""
    manifest = json.loads((root / 'legal/sources/manifest.json').read_text(encoding='utf-8'))
    wanted = {'libheif', 'libde265', 'x265', 'pillow-heif'}
    entries = {e['name']: e for e in manifest['archives'] + manifest['native_archives']
               if e['name'] in wanted}
    if set(entries) != wanted:
        raise ValueError('Pinned HEIC sources missing')
    for name, entry in entries.items():
        path = (root / entry['path']).resolve()
        if not path.is_relative_to((root / 'legal/sources').resolve()):
            raise ValueError('HEIC source outside legal/sources')
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError(f'Changed HEIC source: {name}')
    sources = {}
    for name, entry in entries.items():
        destination = work / 'sources' / name
        destination.mkdir(parents=True)
        with tarfile.open(root / entry['path']) as archive:
            archive.extractall(destination, filter='data')
        children = list(destination.iterdir())
        if len(children) != 1 or not children[0].is_dir():
            raise ValueError(f'Unexpected source layout: {name}')
        sources[name] = children[0]
    return sources, entries


def install_libraries(prefix: Path, work: Path, run) -> dict:
    """Modify only a disposable build venv, retaining the original wheel files."""
    if sys.prefix == sys.base_prefix:
        raise ValueError('HEIC installation requires a disposable virtual environment')
    if importlib.metadata.version('pillow-heif') != '1.3.0':
        raise ValueError('Expected pillow-heif 1.3.0')
    spec = importlib.util.find_spec('_pillow_heif')
    if spec is None or spec.origin is None:
        raise ValueError('pillow-heif extension missing')
    extension = Path(spec.origin).resolve()
    if not extension.is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError('HEIC extension outside build environment')
    vendor = extension.parent / 'pillow_heif.libs'
    if vendor.is_symlink() or not vendor.resolve().is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError('Unsafe HEIC library directory')
    original_hash = digest(extension)
    shutil.copy2(extension, work / extension.name)
    if vendor.exists():
        shutil.move(str(vendor), str(work / 'original-wheel-libraries'))
    vendor.mkdir()
    for library in sorted((prefix / 'lib').glob('*.so*')):
        destination = vendor / library.name
        if library.is_symlink():
            if not library.resolve().is_relative_to(prefix.resolve()):
                raise ValueError('Native library symlink outside prefix')
            destination.symlink_to(os.readlink(library))
        else:
            shutil.copy2(library, destination)
            run(['patchelf', '--set-rpath', '$ORIGIN', str(destination)])
    needed = subprocess.check_output(['patchelf', '--print-needed', str(extension)], text=True)
    old_names = [line for line in needed.splitlines() if re.match(r'libheif(?:-|\.so)', line)]
    if len(old_names) != 1:
        raise ValueError(f'Unexpected libheif dependency: {old_names}')
    run(['patchelf', '--replace-needed', old_names[0], 'libheif.so.1', str(extension)])
    run(['patchelf', '--set-rpath', '$ORIGIN/pillow_heif.libs', str(extension)])
    # Proceso nuevo: no mantengas cargada la biblioteca anterior al verificar su reemplazo.
    code = '''import ctypes,json,pillow_heif
from pathlib import Path
import _pillow_heif
vendor=Path(_pillow_heif.__file__).parent/'pillow_heif.libs'
x265=ctypes.CDLL(str(vendor/'libx265.so.215'))
api=x265.x265_api_get_215
api.restype=ctypes.c_void_p
api.argtypes=[ctypes.c_int]
depths=[depth for depth in (8,10,12) if api(depth)]
if depths != [8,10,12]:
    raise RuntimeError(f'Missing x265 bit depths: {depths}')
print(json.dumps({'info':pillow_heif.libheif_info(),'x265_bit_depths':depths}))
'''
    checked = json.loads(subprocess.check_output([sys.executable, '-c', code], text=True))
    info = checked['info']
    if (info['libheif'] != VERSIONS['libheif']
            or VERSIONS['x265'] not in info.get('HEIF', '')
            or VERSIONS['libde265'] not in info.get('decoders', {}).get('libde265', '')):
        raise ValueError(f'HEIC native versions changed: {info}')
    return {'extension_sha256_before': original_hash, 'extension_sha256_after': digest(extension),
            'versions': info, 'x265_bit_depths': checked['x265_bit_depths'], 'libraries': [
                {'name': p.name, 'sha256': digest(p)} for p in sorted(vendor.glob('*.so*'))
                if not p.is_symlink()]}


def build(work: Path, report: Path, jobs: int = 2, install: bool = True) -> dict:
    """Compila las bibliotecas HEIC en el directorio de trabajo y registra los pasos."""
    if sys.platform != 'linux' or os.uname().machine != 'x86_64':
        raise ValueError('HEIC source build requires Linux x86_64')
    if not 1 <= jobs <= 32:
        raise ValueError('Invalid parallel build count')
    work = work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    result = {'status': 'building', 'versions': VERSIONS, 'commands': [],
              'python': sys.version, 'platform': os.uname().release}
    environment = dict(os.environ)
    prefix = work / 'prefix'
    environment['PKG_CONFIG_PATH'] = str(prefix / 'lib/pkgconfig')
    environment['LD_LIBRARY_PATH'] = str(prefix / 'lib') + os.pathsep + environment.get('LD_LIBRARY_PATH', '')

    def run(command):
        """Ejecuta un comando de compilación y deja constancia de su resultado."""
        result['commands'].append(command)
        subprocess.run(command, env=environment, check=True)

    def cmake(source: Path, directory: Path, flags: list[str], install_target=False):
        """Configura y ejecuta CMake con opciones explícitas para cada dependencia."""
        run(['cmake', '-S', str(source), '-B', str(directory),
             '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
             '-DCMAKE_POLICY_VERSION_MINIMUM=3.5', '-DFETCHCONTENT_FULLY_DISCONNECTED=ON',
             f'-DCMAKE_INSTALL_PREFIX={prefix}', '-DCMAKE_INSTALL_LIBDIR=lib',
             f'-DCMAKE_PREFIX_PATH={prefix}', *flags])
        run(['cmake', '--build', str(directory), '--parallel', str(jobs)])
        if install_target:
            run(['cmake', '--install', str(directory)])

    try:
        result['tools'] = {}
        for tool in ['cmake', 'gcc', 'g++', 'make', 'nasm', 'patch', 'patchelf', 'pkg-config']:
            if not shutil.which(tool):
                raise ValueError(f'Missing build tool: {tool}')
            result['tools'][tool] = subprocess.check_output([tool, '--version'], text=True).splitlines()[0]
        sources, result['sources'] = extract_sources(work)
        x265 = sources['x265']
        # El x265Version.txt archivado está desactualizado. Genera metadatos coherentes
        # con la revisión fijada y la versión observada en el candidato validado.
        version_text = 'repositorychangeset: 1d117be\nreleasetagdistance: 1\nreleasetag: 4.1\n'
        (x265 / 'x265Version.txt').write_text(version_text, encoding='utf-8')
        result['generated_files'] = {'x265Version.txt': version_text}
        for patch_name in ['x265_cmake_1.patch', 'x265_cmake_2.patch']:
            patch = sources['pillow-heif'] / 'libheif' / patch_name
            run(['patch', '-d', str(x265), '-p1', '-i', str(patch)])
        # GCC 15 ya no incluye indirectamente estos tipos enteros faltantes.
        compatibility_patch = ROOT / 'legal/distribution/patches/x265-json11-cstdint.patch'
        run(['patch', '-d', str(x265), '-p1', '-i', str(compatibility_patch)])
        result['additional_patches'] = [
            {'path': compatibility_patch.relative_to(ROOT).as_posix(),
             'sha256': digest(compatibility_patch)}]
        # Usa las dependencias del wheel existente en lugar de enlazar libnuma
        # solo porque la imagen de CI tenga instalados sus encabezados.
        high = ['-DHIGH_BIT_DEPTH=ON', '-DEXPORT_C_API=OFF', '-DENABLE_SHARED=OFF',
                '-DENABLE_CLI=OFF', '-DENABLE_LIBNUMA=OFF']
        for depth in (10, 12):
            directory = work / f'x265-{depth}'
            cmake(x265 / 'source', directory,
                  high + (['-DMAIN12=ON'] if depth == 12 else ['-DENABLE_HDR10_PLUS=ON']))
            shutil.copy2(directory / 'libx265.a', work / f'libx265_main{depth}.a')
        cmake(x265 / 'source', work / 'x265-8', [
            '-DENABLE_CLI=OFF', '-DENABLE_SHARED=ON', '-DENABLE_LIBNUMA=OFF',
            '-DLINKED_10BIT=ON', '-DLINKED_12BIT=ON',
            f'-DEXTRA_LINK_FLAGS=-L{work}', '-DEXTRA_LIB=x265_main10.a;x265_main12.a',
        ], True)
        cmake(sources['libde265'], work / 'de265',
              ['-DENABLE_DECODER=OFF', '-DENABLE_ENCODER=OFF', '-DBUILD_TESTING=OFF'], True)
        cmake(sources['libheif'], work / 'heif', HEIF_FLAGS, True)
        if install:
            result['installed'] = install_libraries(prefix, work, run)
        result['status'] = 'passed'
        return result
    except Exception as error:
        result.update(status='failed', error=str(error))
        raise
    finally:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


def check_package(package: Path) -> None:
    """Comprueba que el paquete use las bibliotecas HEIC recién construidas."""
    if not package.is_dir():
        raise ValueError(f'HEIC package directory missing: {package}')
    unknown = list(package.rglob('libmvec-2-*.so*'))
    if unknown:
        raise ValueError(f'Unidentified prebuilt HEIC compatibility library remains: {unknown}')


def main() -> int:
    """Valida argumentos y coordina la compilación local de las dependencias HEIC."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--no-install', action='store_true')
    parser.add_argument('--check-package', type=Path)
    args = parser.parse_args()
    if args.check_package:
        check_package(args.check_package)
    else:
        if args.work_dir is None or args.report is None:
            parser.error('--work-dir and --report are required for a source build')
        build(args.work_dir, args.report, args.jobs, install=not args.no_install)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
