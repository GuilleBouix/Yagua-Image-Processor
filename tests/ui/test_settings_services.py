from pathlib import Path

from app.ui.frames.settings import services


def test_get_ui_scale_default_si_no_existe(monkeypatch, tmp_path: Path):
    path = tmp_path / "user_settings.json"
    monkeypatch.setattr(services, "_settings_path", lambda: path)

    assert services.get_ui_scale() == 100


def test_get_ui_scale_fallback_si_es_invalida(monkeypatch, tmp_path: Path):
    path = tmp_path / "user_settings.json"
    path.write_text('{"ui_scale": 33}', encoding='utf-8')
    monkeypatch.setattr(services, "_settings_path", lambda: path)

    assert services.get_ui_scale() == 100


def test_set_ui_scale_and_restart_guarda_y_reinicia(monkeypatch, tmp_path: Path):
    path = tmp_path / "user_settings.json"
    monkeypatch.setattr(services, "_settings_path", lambda: path)
    calls = []
    monkeypatch.setattr(services, "restart_app", lambda: calls.append("restart"))

    services.set_ui_scale_and_restart(75)

    assert '"ui_scale": 75' in path.read_text(encoding='utf-8')
    assert calls == ["restart"]
