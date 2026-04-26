from app import main as app_main


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
