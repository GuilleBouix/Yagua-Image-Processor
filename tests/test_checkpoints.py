import copy
import io
import json
import os
from pathlib import Path
import tarfile
import urllib.error

import pytest
import yaml

from scripts.ci import checkpoints as cp


@pytest.fixture
def source(tmp_path, monkeypatch):
    files = {
        'app/version.py': '__version__="2.0.0"',
        'app/main.py': 'original',
        'scripts/ci/test_installer_finish.ps1': 'original installer test',
        'scripts/ci/stages/package.py': 'original packaging',
        'scripts/ci/stages/compile.py': 'original compiler',
        'tests/ui/test_example.py': 'original UI test',
        'new-unknown.cfg': 'unknown',
    }
    for workflow in ('build-windows', 'build-linux', 'validation'):
        files[f'.github/workflows/{workflow}.yml'] = yaml.safe_dump(
            {'jobs': {stage: {'run': stage} for stage in cp.STAGES}})
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    monkeypatch.setattr(cp, 'ROOT', tmp_path)
    monkeypatch.setattr(cp, 'STATE', tmp_path / '.ci-state')
    monkeypatch.setattr(cp, 'tracked', lambda: sorted(files))
    monkeypatch.setattr(cp, 'git', lambda *args: 'a' * 40)
    return tmp_path


def key(stage, dependencies=None):
    return cp.fingerprint(stage, 'windows', '2.0.0', dependencies or {}, {'python': '3.13.12'})[0]


@pytest.mark.parametrize('change,changed,unchanged', [
    ('scripts/ci/test_installer_finish.ps1', 'installer', 'compile'),
    ('scripts/ci/stages/package.py', 'package', 'compile'),
    ('tests/ui/test_example.py', 'ui', 'compile'),
    ('app/main.py', 'compile', 'installer'),
])
def test_changes_invalidate_only_their_inputs(source, change, changed, unchanged):
    before = key(changed), key(unchanged)
    (source / change).write_text('fixed')
    assert key(changed) != before[0]
    assert key(unchanged) == before[1]


def test_unknown_files_and_changed_compiler_environment_invalidate_all(source):
    before = {stage: key(stage) for stage in cp.STAGES}
    (source / 'new-unknown.cfg').write_text('changed')
    assert all(key(stage) != before[stage] for stage in cp.STAGES)
    first = cp.fingerprint('compile', 'linux', '2.0.0', {}, {'image': 'one'})[0]
    second = cp.fingerprint('compile', 'linux', '2.0.0', {}, {'image': 'two'})[0]
    assert first != second


def test_runner_image_patch_is_recorded_but_not_an_abi_change(source, monkeypatch):
    monkeypatch.setenv('ImageOS', 'ubuntu22')
    monkeypatch.setenv('ImageVersion', '20261023.322.3')
    first = cp.fingerprint('compile', 'linux', '2.0.0', {})[0]
    monkeypatch.setenv('ImageVersion', '20261026.341.1')
    assert cp.fingerprint('compile', 'linux', '2.0.0', {})[0] == first
    monkeypatch.setenv('ImageOS', 'ubuntu24')
    assert cp.fingerprint('compile', 'linux', '2.0.0', {})[0] != first


def test_sibling_job_configuration_does_not_recompile_runtime(source):
    before = key('compile')
    file = source / '.github/workflows/build-windows.yml'
    doc = yaml.safe_load(file.read_text())
    doc['jobs']['installer']['run'] = 'fixed automation'
    file.write_text(yaml.safe_dump(doc))
    assert key('compile') == before
    doc['jobs']['compile']['run'] = 'new compiler flags'
    file.write_text(yaml.safe_dump(doc))
    assert key('compile') != before


def test_probe_consumes_portable_and_installer_consumes_setup(source):
    dependencies = {'package': {'files': {'installer/tool.zip': {'sha256': 'portable'},
                                         'installer/setup.exe': {'sha256': 'one'}}}}
    probe, installer = key('probe', dependencies), key('installer', dependencies)
    dependencies['package']['files']['installer/setup.exe']['sha256'] = 'two'
    assert key('probe', dependencies) == probe
    assert key('installer', dependencies) != installer


def make_checkpoint(source, stage='compile', platform='windows'):
    cp.STATE.mkdir(exist_ok=True)
    fingerprint, inputs = cp.fingerprint(stage, platform, '2.0.0', {})
    context = {'stage': stage, 'platform': platform, 'version': '2.0.0', 'fingerprint': fingerprint,
               'inputs': inputs, 'lineage': {}}
    (cp.STATE / 'context.json').write_text(json.dumps(context))
    payload = source / 'dist/tool'
    payload.parent.mkdir(exist_ok=True)
    payload.write_bytes(b'unchanged compiled bytes')
    return cp.save(['dist/tool']), cp.STATE / 'upload'


def test_archive_round_trip_and_corruption_rejected(source):
    receipt, directory = make_checkpoint(source)
    cp.check_receipt(receipt, directory, 'windows')
    restored = source / 'restored'
    restored.mkdir()
    cp.restore(receipt, directory, restored)
    assert (restored / 'dist/tool').read_bytes() == b'unchanged compiled bytes'
    with pytest.raises(ValueError, match='platform'):
        cp.check_receipt(receipt, directory, 'linux')
    with (directory / 'payload.tar').open('ab') as stream:
        stream.write(b'damaged')
    with pytest.raises(ValueError, match='SHA-256'):
        cp.check_receipt(receipt, directory, 'windows')


@pytest.mark.skipif(os.name == 'nt', reason='POSIX executable/symlink semantics')
def test_linux_archive_preserves_execute_bit_and_symlink(source):
    cp.STATE.mkdir()
    (cp.STATE / 'context.json').write_text(json.dumps({'stage': 'compile', 'platform': 'linux'}))
    file = source / 'tool'
    file.write_text('executable')
    file.chmod(0o755)
    (source / 'alias').symlink_to('tool')
    receipt = cp.save(['tool', 'alias'])
    destination = source / 'restored'
    destination.mkdir()
    cp.restore(receipt, cp.STATE / 'upload', destination)
    assert (destination / 'tool').stat().st_mode & 0o111
    assert os.readlink(destination / 'alias') == 'tool'


def test_archive_rejects_paths_outside_destination(tmp_path):
    with tarfile.open(tmp_path / 'payload.tar', 'w') as archive:
        info = tarfile.TarInfo('../escaped')
        info.size = 1
        archive.addfile(info, io.BytesIO(b'x'))
    with pytest.raises(ValueError, match='Unsafe'):
        cp.restore({'files': {}}, tmp_path, tmp_path / 'destination')
    assert not (tmp_path / 'escaped').exists()


@pytest.mark.parametrize('mutation', ['event', 'repository', 'path', 'branch'])
def test_only_main_candidate_and_ci_runs_are_reusable(monkeypatch, mutation):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/yagua')
    run = {'head_repository': {'full_name': 'owner/yagua'}, 'head_branch': 'main',
           'event': 'push', 'path': '.github/workflows/ci.yml'}
    assert cp.trusted(run)
    if mutation == 'event':
        run['event'] = 'pull_request'
    elif mutation == 'repository':
        run['head_repository']['full_name'] = 'outsider/yagua'
    elif mutation == 'path':
        run['path'] = '.github/workflows/checkpoint-selftest.yml'
    else:
        run['head_branch'] = 'feature'
    assert not cp.trusted(run)


@pytest.mark.parametrize('success', [True, False])
def test_a_saved_payload_from_a_failed_job_is_never_approved(monkeypatch, success):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/yagua')
    receipt = {'stage': 'compile', 'platform': 'windows',
               'producer': {'run_id': '100', 'attempt': '1', 'commit': 'abc', 'repository': 'owner/yagua'}}
    monkeypatch.setattr(cp, 'pages', lambda *_: [
        {'name': 'windows / compile / windows / compile', 'conclusion': 'success' if success else 'failure'}])
    assert cp.approved(receipt, {'id': 100, 'head_sha': 'abc'}) is success


@pytest.mark.parametrize('expired,corrupt,expected', [(False, False, True), (True, False, False),
                                                    (False, True, False)])
def test_resume_recovers_only_complete_compatible_outputs(source, monkeypatch, expired, corrupt, expected):
    receipt, directory = make_checkpoint(source)
    original_producer = copy.deepcopy(receipt['producer'])
    monkeypatch.setattr(cp, 'git', lambda *_: 'b' * 40)  # Corrected orchestration commit; runtime inputs unchanged.
    if corrupt:
        (directory / 'payload.tar').write_bytes(b'bad')
    artifact = {'id': 10, 'name': f'checkpoint-windows-compile-{receipt["fingerprint"]}-100-1',
                'expired': expired}
    monkeypatch.setattr(cp, 'candidate_runs', lambda *_: [{'id': 100}])
    monkeypatch.setattr(cp, 'pages', lambda *_: [artifact])
    def receipt_for(_):
        if corrupt:
            raise ValueError('Invalid receipt')
        return copy.deepcopy(receipt), {'id': 100}
    monkeypatch.setattr(cp, 'receipt_for', receipt_for)
    def download(_, target):
        import shutil
        shutil.copytree(directory, target)
    monkeypatch.setattr(cp, 'download', download)
    outputs = {}
    monkeypatch.setattr(cp, 'output', lambda k, v: outputs.update({k: v}))
    cp.prepare('compile', 'windows', '2.0.0', {}, '100', False)
    assert outputs['reused'] == str(expected).lower()
    if expected:
        saved = json.loads((cp.STATE / 'reused.json').read_text())
        assert saved['producer'] == original_producer


def test_force_and_pull_requests_do_not_search_previous_runs(monkeypatch):
    assert cp.candidate_runs('compile', '100', True) == []
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'pull_request')
    assert cp.candidate_runs('compile', '100', False) == []


def test_candidate_waits_only_for_its_platform_stage(monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/yagua')
    monkeypatch.setenv('GITHUB_RUN_ID', '200')
    common = {'head_repository': {'full_name': 'owner/yagua'}, 'head_branch': 'main',
              'head_sha': 'abc', 'event': 'workflow_dispatch', 'status': 'in_progress', 'html_url': 'run'}
    current = {**common, 'id': 200, 'path': '.github/workflows/candidates.yml'}
    ci = {**common, 'id': 100, 'path': '.github/workflows/ci.yml'}
    monkeypatch.setattr(cp, 'api', lambda path: current if path == 'actions/runs/200'
                        else {'workflow_runs': [ci]})
    monkeypatch.setattr(cp, 'pages', lambda *_: [
        {'name': 'windows / quality', 'status': 'completed'},
        {'name': 'linux / ui', 'status': 'in_progress'}])
    monkeypatch.setattr(cp.time, 'sleep', lambda *_: pytest.fail('Other-platform UI must not block quality'))
    assert [run['id'] for run in cp.candidate_runs('quality', '', False, 'windows')] == [200, 100]


def test_recovery_bookkeeping_change_does_not_invalidate_ui_or_compilation(source):
    file = source / 'scripts/ci/checkpoints.py'
    file.write_text('old transport')
    before = key('compile'), key('ui'), key('core')
    # This helper is classified as CI tooling, not a runtime/UI input.
    names = cp.tracked() + ['scripts/ci/checkpoints.py']
    original = cp.tracked
    try:
        cp.tracked = lambda: names
        before = key('compile'), key('ui'), key('core')
        file.write_text('network retry fix')
        assert (key('compile'), key('ui')) == before[:2]
        assert key('core') != before[2]
    finally:
        cp.tracked = original


def test_transient_503_retries_transport_without_becoming_a_cache_miss(monkeypatch):
    monkeypatch.setattr(cp.time, 'sleep', lambda *_: None)
    calls = []
    def request():
        calls.append(1)
        if len(calls) < 3:
            raise urllib.error.HTTPError('https://artifact', 503, 'Egress limit', {}, None)
        return 'payload'
    assert cp.retry_network(request) == 'payload'
    assert len(calls) == 3


def test_persistent_transport_failure_stops_instead_of_rebuilding(monkeypatch):
    monkeypatch.setattr(cp.time, 'sleep', lambda *_: None)
    def unavailable():
        raise urllib.error.HTTPError('https://artifact', 503, 'Egress limit', {}, None)
    with pytest.raises(RuntimeError, match='without rebuilding'):
        cp.retry_network(unavailable)


def test_checkpoint_transport_failure_never_falls_back_to_execution(source, monkeypatch):
    receipt, _ = make_checkpoint(source)
    artifact = {'id': 10, 'name': f'checkpoint-windows-compile-{receipt["fingerprint"]}-100-1', 'expired': False}
    monkeypatch.setattr(cp, 'candidate_runs', lambda *_: [{'id': 100}])
    monkeypatch.setattr(cp, 'pages', lambda *_: [artifact])
    monkeypatch.setattr(cp, 'receipt_for', lambda *_: (receipt, {'id': 100}))
    def outage(*_):
        raise RuntimeError('Transport unavailable')
    monkeypatch.setattr(cp, 'download', outage)
    with pytest.raises(RuntimeError, match='Transport unavailable'):
        cp.prepare('compile', 'windows', '2.0.0', {}, '100', False)


def test_assertions_and_authentication_are_not_automatically_retried(monkeypatch):
    monkeypatch.setattr(cp.time, 'sleep', lambda *_: pytest.fail('Must not retry'))
    with pytest.raises(AssertionError):
        cp.retry_network(lambda: (_ for _ in ()).throw(AssertionError('bad test')))
    def unauthorized():
        raise urllib.error.HTTPError('https://artifact', 403, 'Forbidden', {}, None)
    with pytest.raises(RuntimeError, match='refused'):
        cp.retry_network(unauthorized)


def test_failed_ci_assertion_is_not_automatically_run_again(source, monkeypatch):
    monkeypatch.setenv('GITHUB_SHA', 'abc')
    run = {'id': 100, 'path': '.github/workflows/ci.yml', 'head_sha': 'abc', 'conclusion': 'failure'}
    monkeypatch.setattr(cp, 'candidate_runs', lambda *_: [run])
    monkeypatch.setattr(cp, 'pages', lambda path, key: [] if key == 'artifacts' else [
        {'name': 'windows / ui', 'conclusion': 'failure'}])
    with pytest.raises(RuntimeError, match='Existing CI failed'):
        cp.prepare('ui', 'windows', '2.0.0', {}, '', False)


def test_pipeline_requires_all_validation_and_package_jobs():
    root = Path(__file__).resolve().parents[1] / '.github/workflows'
    for platform in ('windows', 'linux'):
        workflow = yaml.safe_load((root / f'build-{platform}.yml').read_text())
        jobs = workflow['jobs']
        assert jobs['compile']['needs'] == 'validate'
        assert jobs['package']['needs'] == 'compile'
        assert jobs['probe']['needs'] == 'package'
        assert {'validate', 'package', 'probe', 'sources'} <= set(jobs['deliver']['needs'])
        if platform == 'windows':
            assert 'installer' in jobs['deliver']['needs']
