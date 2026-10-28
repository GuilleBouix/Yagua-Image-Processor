"""Pruebas de interfaz para app main y sus estados principales."""

from app import app as app_module
from app import main as app_main
from app.ui import main_window


def test_main_aplica_escala_antes_de_crear_app(monkeypatch, tmp_path):
    events = []

    monkeypatch.setattr(app_main, "settings_path", lambda: tmp_path / "user_settings.json")
    monkeypatch.setattr(app_main.logging, "basicConfig", lambda **kwargs: None)
    monkeypatch.setattr(app_main.ctk, "set_appearance_mode", lambda mode: events.append(("appearance", mode)))
    monkeypatch.setattr(app_main.ctk, "set_default_color_theme", lambda theme: events.append(("theme", theme)))
    monkeypatch.setattr(app_main, "apply_ui_scale", lambda: events.append(("scale", None)))

    class FakeApp:
        def __init__(self):
            events.append(("app", None))

        def mainloop(self):
            events.append(("mainloop", None))

    monkeypatch.setattr(app_main, "YaguaApp", FakeApp)

    app_main.main()

    assert events == [
        ("appearance", "dark"),
        ("theme", "blue"),
        ("scale", None),
        ("app", None),
        ("mainloop", None),
    ]


def test_dock_reopen_registra_y_ejecuta_callback_en_macos(monkeypatch):
    commands = {}
    calls = []

    class FakeWindow:
        def createcommand(self, name, callback):
            commands[name] = callback

        def _on_dock_click(self):
            calls.extend(("deiconify", "lift", "focus"))

    window = FakeWindow()
    monkeypatch.setattr(app_module.sys, "platform", "darwin")

    app_module.YaguaApp._setup_dock_reopen(window)
    commands["tk::mac::ReopenApplication"]()

    assert calls == ["deiconify", "lift", "focus"]


def test_main_window_tiene_traducciones_para_banner_de_actualizacion():
    assert main_window.t("updates_available")


def test_unwritable_log_directory_does_not_block_startup(monkeypatch, tmp_path):
    from pathlib import Path
    calls = []
    def denied(*args, **kwargs):
        raise PermissionError('read-only profile')
    class FakeApp:
        def mainloop(self):
            calls.append('started')
    monkeypatch.setattr(app_main, 'settings_path', lambda: tmp_path / 'settings.json')
    monkeypatch.setattr(Path, 'mkdir', denied)
    monkeypatch.setattr(app_main.logging, 'basicConfig', lambda **kwargs: None)
    monkeypatch.setattr(app_main, 'YaguaApp', FakeApp)
    monkeypatch.setattr(app_main, 'apply_ui_scale', lambda: None)
    app_main.main()
    assert calls == ['started']
