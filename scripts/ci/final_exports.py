"""Idempotent final uploads: retain and verify immutable exports on partial reruns."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

from scripts.ci.checkpoints import api, digest, output, pages


def verify_export(archive: Path, manifest_name: str, expected: dict) -> None:
    with zipfile.ZipFile(archive) as zipped:
        # upload-artifact chooses a common root from the declared paths, even
        # when some platform-specific paths do not exist. Source-review exports
        # can therefore have their manifest at the root or under reports/.
        layouts = {manifest_name}
        if Path(manifest_name).name.endswith('-sources.json'):
            layouts.update({Path(manifest_name).name, 'reports/' + Path(manifest_name).name})
        present = sorted(layouts.intersection(zipped.namelist()))
        if len(present) != 1:
            raise ValueError('Missing or ambiguous source/candidate manifest in existing export')
        manifest_name = present[0]
        recorded = json.loads(zipped.read(manifest_name))
        if recorded != expected:
            raise ValueError('Existing export differs; start a new run with resume_run_id instead of overwriting it')
        parent = Path(manifest_name).parent
        for artifact in expected['artifacts']:
            name = (parent / artifact['name']).as_posix()
            with zipped.open(name) as stream:
                checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
            if zipped.getinfo(name).file_size != artifact['bytes'] or checksum != artifact['sha256']:
                raise ValueError('Existing final artifact checksum mismatch')


def main():
    platform, version = os.environ['STAGE_PLATFORM'], os.environ['STAGE_VERSION']
    artifacts = pages(f'actions/runs/{os.environ["GITHUB_RUN_ID"]}/artifacts', 'artifacts')
    candidate = ('installer/candidate-windows.json' if platform == 'windows' else 'reports/candidate-linux.json')
    sources = f'reports/candidate-{platform}-sources.json'
    checks = [('candidate', f'{platform}-validated-{version}', candidate,
               candidate if platform == 'windows' else 'candidate-linux.json'),
              ('sources', f'{platform}-source-materials-{version}', sources,
               sources if platform == 'windows' else f'candidate-{platform}-sources.json')]
    for kind, name, local, archived in checks:
        output(kind + '_exists', 'false')
        existing = [artifact for artifact in artifacts if artifact['name'] == name and not artifact['expired']]
        if not existing:
            continue
        artifact = existing[0]
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / 'export.zip'
            with api(artifact['archive_download_url'], raw=True) as response, archive.open('wb') as stream:
                shutil.copyfileobj(response, stream)
            if artifact.get('digest') != 'sha256:' + digest(archive):
                raise ValueError('Existing export archive checksum mismatch')
            verify_export(archive, archived, json.loads(Path(local).read_text(encoding='utf-8')))
        output(kind + '_exists', 'true')


if __name__ == '__main__':
    main()
