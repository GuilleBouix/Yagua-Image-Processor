"""Priority UI validation must cover all tests and never checkpoint a failure."""

import subprocess
from xml.etree import ElementTree as ET

import pytest

from scripts.ci import checkpoints, partitions
from scripts.ci.stages import ui


@pytest.mark.parametrize('mutation', ['missing', 'duplicate'])
def test_priority_partition_rejects_missing_or_repeated_tests(monkeypatch, mutation):
    priority, remaining = partitions.ui_selections()
    selections = {
        (): {'core', 'first', 'second'},
        ('--ignore=tests/ui',): {'core'},
        ('tests/ui',): {'first', 'second'},
        priority: {'first'},
        remaining: set() if mutation == 'missing' else {'first', 'second'},
    }
    monkeypatch.setattr(partitions, 'collected', lambda *args: selections[args])
    with pytest.raises(ValueError, match='priority/rest'):
        partitions.main()


def test_partition_recipe_invalidates_ui_checkpoint():
    path = 'scripts/ci/partitions.py'
    assert path in checkpoints.stage_files('ui', 'linux', [path])


@pytest.mark.parametrize('attribute', ['failures', 'errors', 'tests'])
def test_merge_rejects_failed_or_empty_results(tmp_path, attribute):
    report = tmp_path / 'ui.xml'
    report.write_text(f'<testsuites><testsuite tests="{0 if attribute == "tests" else 1}" '
                      f'{attribute + "=\"1\"" if attribute != "tests" else ""}/></testsuites>')
    with pytest.raises(ValueError):
        ui.merge_reports([report], tmp_path / 'combined.xml')
    assert not (tmp_path / 'combined.xml').exists()


def test_stage_stops_after_priority_failure_and_keeps_existing_checkpoints(tmp_path, monkeypatch):
    calls, saved = [], []
    monkeypatch.setattr(ui, 'REPORTS', tmp_path)
    monkeypatch.setattr(ui, 'test_dependencies', lambda: None)
    monkeypatch.setattr(ui, 'save', lambda *args: saved.append(args))
    def fail(*args):
        calls.append(args)
        raise subprocess.CalledProcessError(1, args)
    monkeypatch.setattr(ui, 'xvfb', fail)
    with pytest.raises(subprocess.CalledProcessError):
        ui.main()
    assert len(calls) == 1
    assert not saved


def test_reports_preserve_all_successful_cases(tmp_path):
    paths = []
    for index, count in enumerate((3, 7)):
        path = tmp_path / f'{index}.xml'
        path.write_text(f'<testsuites><testsuite tests="{count}" failures="0" errors="0"/></testsuites>')
        paths.append(path)
    merged = tmp_path / 'ui.xml'
    ui.merge_reports(paths, merged)
    assert sum(int(suite.get('tests')) for suite in ET.parse(merged).getroot()) == 10
