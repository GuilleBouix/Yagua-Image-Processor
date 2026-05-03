from __future__ import annotations

from dataclasses import dataclass

import customtkinter as ctk

from app.ui import main_window as main_window_module


@dataclass(frozen=True)
class _Spec:
    key: str
    frame_import: str = "fake.module:FakeFrame"


def _host(view):
    return getattr(view, "_parent_frame", view)


class _FakeSidebar(ctk.CTkFrame):
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.on_select = on_select
        self.active = "sentinel"

    def set_active(self, key):
        self.active = key


class _BaseFakeView(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)
        self.shown_calls = 0
        self.hidden_calls = 0
        self.status = ctk.StringVar(value="idle")

    def on_view_shown(self):
        self.shown_calls += 1

    def on_view_hidden(self):
        self.hidden_calls += 1


class _FakeHomeView(_BaseFakeView):
    pass


class _FakeSettingsView(_BaseFakeView):
    pass


class _FakeLqipView(_BaseFakeView):
    pass


class _FakeRemoveBgView(_BaseFakeView):
    def __init__(self, parent):
        super().__init__(parent)
        self.after(0, lambda: self.status.set("ready"))


class _FakeOcrView(_BaseFakeView):
    def __init__(self, parent):
        super().__init__(parent)
        self.after(0, lambda: self.status.set("loaded"))


def _setup_main_window(monkeypatch, ui_root):
    specs = [_Spec("settings"), _Spec("lqip"), _Spec("remove_bg"), _Spec("ocr")]
    frame_map = {
        "settings": _FakeSettingsView,
        "lqip": _FakeLqipView,
        "remove_bg": _FakeRemoveBgView,
        "ocr": _FakeOcrView,
    }

    monkeypatch.setattr(main_window_module, "Sidebar", _FakeSidebar)
    monkeypatch.setattr(main_window_module, "HomeFrame", _FakeHomeView)
    monkeypatch.setattr(main_window_module, "iter_enabled_modules", lambda: iter(specs))
    monkeypatch.setattr(main_window_module, "get_module_spec", lambda key: _Spec(key))
    monkeypatch.setattr(main_window_module, "load_frame_class", lambda spec: frame_map[spec.key])

    window = main_window_module.MainWindow(ui_root)
    ui_root.update_idletasks()
    ui_root.update()
    return window


def test_main_window_muestra_una_sola_vista_activa(monkeypatch, ui_root):
    window = _setup_main_window(monkeypatch, ui_root)

    home_host = _host(window._home)
    assert home_host.winfo_manager() == "place"
    assert window._home.shown_calls == 1
    assert window.sidebar.active is None

    sequence = ["settings", "lqip", "remove_bg", "ocr", "settings"]
    for key in sequence:
        previous_view = window._active_view
        window.show_module(key)
        ui_root.update_idletasks()
        ui_root.update()

        current_view = window.frames[key]
        current_host = _host(current_view)

        assert window._active_view_key == key
        assert window._active_view is current_view
        assert current_host.winfo_manager() == "place"
        assert window.sidebar.active == key

        if previous_view is not None and previous_view is not current_view:
            assert _host(previous_view).winfo_manager() == ""

    hidden_hosts = [
        _host(view).winfo_manager()
        for module_key, view in window.frames.items()
        if module_key != "settings" and view is not None
    ]
    assert hidden_hosts == ["", "", ""]
    assert home_host.winfo_manager() == ""


def test_main_window_reutiliza_frames_lazy_loaded(monkeypatch, ui_root):
    window = _setup_main_window(monkeypatch, ui_root)

    window.show_module("settings")
    ui_root.update_idletasks()
    ui_root.update()
    first_settings = window.frames["settings"]

    window.show_module("lqip")
    ui_root.update_idletasks()
    ui_root.update()

    window.show_module("settings")
    ui_root.update_idletasks()
    ui_root.update()

    assert window.frames["settings"] is first_settings
    assert first_settings.shown_calls == 2
    assert first_settings.hidden_calls == 1


def test_main_window_callbacks_tardios_no_reactivan_vista_oculta(monkeypatch, ui_root):
    window = _setup_main_window(monkeypatch, ui_root)

    window.show_module("remove_bg")
    ui_root.update_idletasks()
    ui_root.update()
    remove_bg_view = window.frames["remove_bg"]

    window.show_module("settings")
    ui_root.update_idletasks()
    ui_root.update()

    ui_root.update_idletasks()
    ui_root.update()

    assert remove_bg_view.status.get() == "ready"
    assert _host(remove_bg_view).winfo_manager() == ""
    assert window._active_view_key == "settings"

    window.show_module("ocr")
    ui_root.update_idletasks()
    ui_root.update()
    ocr_view = window.frames["ocr"]

    window.show_module("settings")
    ui_root.update_idletasks()
    ui_root.update()
    ui_root.update_idletasks()
    ui_root.update()

    assert ocr_view.status.get() == "loaded"
    assert _host(ocr_view).winfo_manager() == ""
    assert window._active_view_key == "settings"
