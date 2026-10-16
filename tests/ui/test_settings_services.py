import json
import os
from pathlib import Path
import sys

import pytest

from app.ui.frames.settings import services
from app.languages import AVAILABLE_LANGUAGES
from app.utils.settings import load_settings


def test_get_ui_scale_default_si_no_existe(monkeypatch, tmp_path: Path):
    path = tmp_path / "user_settings.json"
    monkeypatch.setattr(services, "_settings_path", lambda: path)

    assert services.get_ui_scale() == 100


def test_get_ui_scale_fallback_si_es_invalida(monkeypatch, tmp_path: Path):
    path = tmp_path / "user_settings.json"
    path.write_text('{"ui_scale": 33}', encoding='utf-8')
    monkeypatch.setattr(services, "_settings_path", lambda: path)

    assert services.get_ui_scale() == 100


@pytest.mark.parametrize('language', list(AVAILABLE_LANGUAGES))
def test_apply_settings_guarda_todo_y_reinicia_una_vez(monkeypatch, tmp_path: Path, language):
    path = tmp_path / "user_settings.json"
    path.write_text('{"keep": "value"}', encoding='utf-8')
    monkeypatch.setattr(services, "_settings_path", lambda: path)
    calls = []
    monkeypatch.setattr(services, "restart_app", lambda: calls.append("restart"))

    services.apply_settings_and_restart(
        language=language,
        theme='Dracula',
        ui_scale=75,
        visible_modules=['ocr', 'unknown'],
    )

    assert json.loads(path.read_text(encoding='utf-8')) == {
        'keep': 'value',
        'language': language,
        'theme': 'Dracula',
        'ui_scale': 75,
        'visible_modules': ['ocr', 'settings'],
    }
    assert calls == ['restart']
    assert load_settings(path)['language'] == language


@pytest.mark.parametrize(
    ('field', 'value'),
    [('language', 'Klingon'), ('theme', 'Unknown'), ('ui_scale', 33)],
)
def test_apply_settings_rechaza_valores_invalidos(monkeypatch, tmp_path: Path, field, value):
    path = tmp_path / "user_settings.json"
    monkeypatch.setattr(services, "_settings_path", lambda: path)
    values = {
        'language': 'Español',
        'theme': 'Default',
        'ui_scale': 100,
        'visible_modules': ['settings'],
    }
    values[field] = value

    with pytest.raises(ValueError):
        services.apply_settings_and_restart(**values)

    assert not path.exists()


def test_restart_command_usa_appimage_original(monkeypatch, tmp_path: Path):
    appimage = tmp_path / 'Yagua.AppImage'
    appimage.touch()
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'argv', ['/tmp/.mount_Yagua/usr/lib/yagua/Yagua', '--test'])

    command = services._restart_command({'APPIMAGE': str(appimage)})

    assert command == [str(appimage), '--test']


def test_restart_command_frozen_sin_appimage_usa_executable(monkeypatch):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'argv', ['Yagua', '--test'])
    monkeypatch.setattr(sys, 'executable', '/opt/Yagua/Yagua')

    assert services._restart_command({}) == ['/opt/Yagua/Yagua', '--test']


def test_restart_command_desarrollo_usa_python_y_script(monkeypatch, tmp_path: Path):
    script = tmp_path / 'main.py'
    monkeypatch.delattr(sys, 'frozen', raising=False)
    monkeypatch.setattr(sys, 'argv', [str(script), '--test'])
    monkeypatch.setattr(sys, 'executable', '/usr/bin/python3')

    assert services._restart_command({}) == ['/usr/bin/python3', str(script.resolve()), '--test']


def test_restart_environment_limpia_montaje_y_conserva_display():
    environment = services._restart_environment({
        'APPDIR': '/tmp/.mount_Yagua',
        'APPIMAGE': '/home/user/Yagua.AppImage',
        'ARGV0': 'Yagua',
        'LD_LIBRARY_PATH': '/tmp/.mount_Yagua/usr/lib',
        'LD_LIBRARY_PATH_ORIG': '/usr/local/lib',
        'DISPLAY': ':0',
        'WAYLAND_DISPLAY': 'wayland-0',
    })

    assert environment == {
        'LD_LIBRARY_PATH': '/usr/local/lib',
        'DISPLAY': ':0',
        'WAYLAND_DISPLAY': 'wayland-0',
    }


def test_restart_environment_de_desarrollo_no_se_modifica():
    original = {'LD_LIBRARY_PATH': '/opt/custom', 'DISPLAY': ':0'}

    assert services._restart_environment(original) == original


def test_restart_app_abre_una_instancia(monkeypatch):
    calls = []
    monkeypatch.setattr(services, '_restart_command', lambda: ['Yagua.AppImage'])
    monkeypatch.setattr(services, '_restart_environment', lambda: {'DISPLAY': ':0'})
    monkeypatch.setattr(
        services.subprocess,
        'Popen',
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    with pytest.raises(SystemExit):
        services.restart_app()

    assert len(calls) == 1
    assert calls[0][0] == ['Yagua.AppImage']
    assert calls[0][1]['env'] == {'DISPLAY': ':0'}
    assert calls[0][1].get('start_new_session', False) is (os.name != 'nt')
