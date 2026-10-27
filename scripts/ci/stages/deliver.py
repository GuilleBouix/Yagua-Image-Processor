import json
from pathlib import Path
import shutil

from scripts.ci import candidate_manifest
from scripts.ci.stages.common import PLATFORM, REPORTS, ROOT, VERSION, python


def main():
    context = json.loads((ROOT / '.ci-state/context.json').read_text())
    lineage = context['lineage']
    required = {'quality', 'core', 'ui', 'compile', 'package', 'probe', 'sources'}
    if PLATFORM == 'windows':
        required.add('installer')
    if not required <= lineage.keys():
        raise ValueError(f'Missing approved stages: {required - lineage.keys()}')
    if PLATFORM == 'windows':
        artifacts = [ROOT / f'installer/Yagua_Setup_{VERSION}.exe',
                     ROOT / f'installer/Yagua_Portable_{VERSION}.zip']
        manifest_path = ROOT / 'installer/candidate-windows.json'
        notes = python('scripts/ci/extract_release_notes.py', VERSION, capture_output=True, text=True)
        (ROOT / 'release_notes.md').write_text(notes.stdout, encoding='utf-8')
    else:
        artifact = ROOT / f'dist/linux-release/Yagua-{VERSION}-x86_64.AppImage'
        for path in (artifact, artifact.with_name(artifact.name + '.sha256')):
            shutil.copy2(path, REPORTS / path.name)
        artifacts = [REPORTS / artifact.name]
        manifest_path = REPORTS / 'candidate-linux.json'
        shutil.copy2(ROOT / 'dist/linux-release/linux-heic-native.json', REPORTS / 'linux-heic-native.json')
    manifest = candidate_manifest.create(VERSION, artifacts, provenance=lineage)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    sources = REPORTS / f'Yagua-{VERSION}-source-materials.tar.xz'
    source_manifest = candidate_manifest.create(VERSION, [sources], provenance=lineage)
    (REPORTS / f'candidate-{PLATFORM}-sources.json').write_text(json.dumps(source_manifest, indent=2) + '\n',
                                                            encoding='utf-8')
    candidate_manifest.verify(manifest, Path(manifest_path).parent, VERSION,
                              manifest['source']['commit'], str(manifest['build']['run_id']))


if __name__ == '__main__':
    main()
