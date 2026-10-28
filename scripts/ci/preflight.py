"""Fast source checks before downloading environments or compiling candidates."""
# Ejecuta comprobaciones rápidas antes de preparar entornos o compilar.
import argparse
import ast
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.ci.candidate_manifest import check_source_version  # noqa: E402
from scripts.ci.source_materials import safe_path, verify  # noqa: E402
from scripts.licensing import validate_catalog  # noqa: E402


def check_version(version: str, platform: str, root: Path = ROOT) -> None:
    """Valida que la versión candidata coincida con los metadatos del instalador o release."""
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?', version):
        raise ValueError('Invalid candidate version')
    check_source_version(version)
    if platform == 'windows':
        fields = dict(line.split('=', 1) for line in (root / 'Yagua.iss').read_text(encoding='utf-8').splitlines()
                      if '=' in line and not line.lstrip().startswith(';'))
        if fields.get('AppVersion') != version or fields.get('OutputBaseFilename') != f'Yagua_Setup_{version}':
            raise ValueError('Installer version/output filename differs from the candidate')
    if platform == 'linux':
        import urllib.error
        from scripts.ci.checkpoints import api
        for endpoint in (f'releases/tags/linux-v{version}', f'git/ref/tags/linux-v{version}'):
            try:
                api(endpoint)
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
            else:
                raise ValueError('Linux version already has a release or tag; use a new version')


def check_stage_initializer(text: str) -> None:
    # Este marcador de paquete es intencionalmente inerte. Los helpers ejecutables
    # van en common.py, que es una entrada de cada etapa que los utiliza.
    """Exige que los inicializadores de etapas sigan siendo declarativos."""
    tree = ast.parse(text)
    if any(not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)) for node in tree.body):
        raise ValueError('Keep the stage initializer declarative; put executable helpers in common.py')


def main():
    """Ejecuta validaciones tempranas antes de descargar dependencias o compilar."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version')
    parser.add_argument('--platform', choices=['windows', 'linux'], default='')
    args = parser.parse_args()
    check_stage_initializer((ROOT / 'scripts/ci/stages/__init__.py').read_text(encoding='utf-8'))
    if args.version:
        check_version(args.version, args.platform)
    validate_catalog(ROOT)
    manifest = json.loads((ROOT / 'legal/distribution/materials.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        if 'repository_path' in entry:
            verify(safe_path(ROOT, entry['repository_path']), entry)
    print('Source version, legal resources and local source-material hashes passed.')


if __name__ == '__main__':
    main()
