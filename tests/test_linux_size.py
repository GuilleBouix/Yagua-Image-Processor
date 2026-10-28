"""Comprueba el límite de tamaño sin crear archivos gigantes para probar el umbral."""

import pytest

from scripts.ci import check_linux_size as checker


def test_authorized_two_gb_ceiling_accepts_current_linux_package():
    assert checker.MAX_BYTES == 2_000_000_000
    assert checker.within_budget(1_527_547_135)


@pytest.mark.parametrize(('size', 'expected'), [
    (-1, False), (0, True), (checker.MAX_BYTES - 1, True), (checker.MAX_BYTES, False),
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
