"""Budget checks must not allocate huge files to exercise the boundary."""

import pytest

from scripts.ci import check_linux_size as checker


@pytest.mark.parametrize(('size', 'expected'), [
    (0, True), (checker.MAX_BYTES - 1, True), (checker.MAX_BYTES, False),
    (checker.MAX_BYTES + 1, False),
])
def test_budget_boundary(size, expected):
    assert checker.within_budget(size) is expected


def test_rejects_oversized_artifact_without_allocating_it(monkeypatch, tmp_path):
    monkeypatch.setattr(checker, 'artifact_size', lambda _: checker.MAX_BYTES)
    with pytest.raises(SystemExit) as error:
        checker.main([str(tmp_path)])
    assert error.value.code == 1


def test_counts_nested_files(tmp_path):
    (tmp_path / 'nested').mkdir()
    (tmp_path / 'nested/data').write_bytes(b'1234')
    (tmp_path / 'other').write_bytes(b'12')
    assert checker.artifact_size(tmp_path) == 6


def test_missing_artifact_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        checker.artifact_size(tmp_path / 'missing')
