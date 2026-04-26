from app.ui import scale


def test_apply_ui_scale_100(monkeypatch):
    monkeypatch.setattr(scale, "_load_settings", lambda: {"ui_scale": 100})
    calls = []
    monkeypatch.setattr(scale.ctk, "set_widget_scaling", lambda value: calls.append(("widget", value)))
    monkeypatch.setattr(scale.ctk, "set_window_scaling", lambda value: calls.append(("window", value)))

    scale.apply_ui_scale()

    assert calls == [("widget", 1.0), ("window", 1.0)]


def test_apply_ui_scale_75(monkeypatch):
    monkeypatch.setattr(scale, "_load_settings", lambda: {"ui_scale": 75})
    calls = []
    monkeypatch.setattr(scale.ctk, "set_widget_scaling", lambda value: calls.append(("widget", value)))
    monkeypatch.setattr(scale.ctk, "set_window_scaling", lambda value: calls.append(("window", value)))

    scale.apply_ui_scale()

    assert calls == [("widget", 0.75), ("window", 0.75)]


def test_apply_ui_scale_50(monkeypatch):
    monkeypatch.setattr(scale, "_load_settings", lambda: {"ui_scale": 50})
    calls = []
    monkeypatch.setattr(scale.ctk, "set_widget_scaling", lambda value: calls.append(("widget", value)))
    monkeypatch.setattr(scale.ctk, "set_window_scaling", lambda value: calls.append(("window", value)))

    scale.apply_ui_scale()

    assert calls == [("widget", 0.5), ("window", 0.5)]
