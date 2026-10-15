import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from app.ui.operations import OperationCoordinator


def test_coordinator_allows_only_one_global_operation():
    coordinator = OperationCoordinator()
    first_owner = object()
    second_owner = object()

    first = coordinator.begin(first_owner, "convert")

    assert first is not None
    assert coordinator.begin(second_owner, "resize") is None
    assert coordinator.is_busy()
    assert coordinator.is_busy(first_owner)
    assert not coordinator.is_busy(second_owner)

    assert coordinator.finish(first.id)
    assert coordinator.active is None
    assert not coordinator.is_busy()


def test_stale_completion_cannot_release_new_operation():
    coordinator = OperationCoordinator()
    first = coordinator.begin(object(), "first")
    assert first is not None
    assert coordinator.finish(first.id)

    second = coordinator.begin(object(), "second")
    assert second is not None

    assert not coordinator.finish(first.id)
    assert coordinator.active == second


def test_simultaneous_starts_grant_exactly_one_slot():
    coordinator = OperationCoordinator()
    owners = [object() for _ in range(16)]
    with ThreadPoolExecutor(max_workers=len(owners)) as pool:
        operations_started = list(pool.map(lambda owner: coordinator.begin(owner, "batch"), owners))

    assert sum(operation is not None for operation in operations_started) == 1


def test_submit_entrega_resultado_y_libera_slot_en_drain():
    coordinator = OperationCoordinator()
    completed = []
    owner = object()
    assert coordinator.submit(owner, "work", lambda: 42, completed.append, completed.append)

    for _ in range(100):
        if not coordinator._completions.empty():
            break
        Event().wait(0.01)
    coordinator.drain()

    assert completed == [42]
    assert coordinator.active is None


def test_submit_entrega_erro_y_libera_slot():
    coordinator = OperationCoordinator()
    errors = []
    owner = object()
    assert coordinator.submit(
        owner, "work", lambda: (_ for _ in ()).throw(ValueError("bad input")),
        lambda result: None, errors.append,
    )
    for _ in range(100):
        if not coordinator._completions.empty():
            break
        Event().wait(0.01)
    coordinator.drain()

    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
    assert coordinator.active is None


def test_callback_failure_does_not_stop_deliveries():
    coordinator = OperationCoordinator()
    delivered = []
    owner = object()
    coordinator.post(owner, lambda: (_ for _ in ()).throw(ValueError('UI error')))
    coordinator.post(owner, lambda: delivered.append('next'))
    coordinator.drain()
    assert delivered == ['next']


def test_destroyed_owner_receives_no_callbacks():
    coordinator = OperationCoordinator()
    delivered = []
    coordinator.post(object(), lambda: delivered.append('unexpected'))
    coordinator.drain(lambda owner: False)
    assert delivered == []


def test_generated_state_sequences():
    import random
    for seed in range(100):
        randomizer = random.Random(seed)
        coordinator = OperationCoordinator()
        active = None
        stale = []
        for _ in range(100):
            action = randomizer.randrange(3)
            if action == 0:
                operation = coordinator.begin(object(), 'generated')
                assert (operation is None) == (active is not None)
                if operation:
                    active = operation
            elif action == 1 and active:
                assert coordinator.finish(active.id)
                stale.append(active.id)
                active = None
            elif stale:
                assert not coordinator.finish(randomizer.choice(stale))
            assert coordinator.active == active


def test_thread_start_failure_restores_coordinator(monkeypatch):
    coordinator = OperationCoordinator()
    errors = []
    def fail(self):
        raise RuntimeError('No worker available')
    monkeypatch.setattr('app.ui.operations.Thread.start', fail)
    assert not coordinator.submit(object(), 'work', lambda: None, lambda result: None, errors.append)
    assert coordinator.active is None
    assert len(errors) == 1



def test_close_waits_for_current_write_and_can_be_cancelled(monkeypatch):
    from app import app as app_module
    coordinator = OperationCoordinator()
    monkeypatch.setattr(app_module, 'operations', coordinator)
    class Window:
        _close_after_operation = False
        destroyed = False
        callbacks = []
        def destroy(self):
            self.destroyed = True
        def after(self, delay, callback):
            self.callbacks.append(callback)
        def _finish_close_when_idle(self):
            app_module.YaguaApp._finish_close_when_idle(self)
    window = Window()
    operation = coordinator.begin(object(), 'write')
    assert operation is not None
    monkeypatch.setattr(app_module.messagebox, 'askyesno', lambda *args, **kwargs: False)
    app_module.YaguaApp._request_close(window)
    assert not window.destroyed and not window.callbacks
    monkeypatch.setattr(app_module.messagebox, 'askyesno', lambda *args, **kwargs: True)
    app_module.YaguaApp._request_close(window)
    window.callbacks.pop(0)()
    assert not window.destroyed
    coordinator.finish(operation.id)
    window.callbacks.pop(0)()
    assert window.destroyed


def test_restart_waits_for_current_write(monkeypatch):
    import tkinter
    from app.ui.frames.settings import services
    from app.ui import operations as operation_module
    coordinator = OperationCoordinator()
    monkeypatch.setattr(operation_module, 'operations', coordinator)
    callbacks, starts = [], []
    class Root:
        def after(self, delay, callback):
            callbacks.append(callback)
    monkeypatch.setattr(tkinter, '_default_root', Root(), raising=False)
    monkeypatch.setattr('tkinter.messagebox.askyesno', lambda *args, **kwargs: True)
    monkeypatch.setattr(services, '_restart_command', lambda: ['fake-executable'])
    monkeypatch.setattr(services.subprocess, 'Popen', lambda *args, **kwargs: starts.append(args))
    monkeypatch.setattr(services.sys, 'exit', lambda code: None)
    operation = coordinator.begin(object(), 'write')
    assert operation is not None
    services.restart_app()
    assert not starts
    callbacks.pop(0)()
    assert not starts
    coordinator.finish(operation.id)
    callbacks.pop(0)()
    assert len(starts) == 1


def test_view_destroy_cancels_owned_timers(ui_root):
    from app.ui.frames.compress.frame import CompressFrame
    frame = CompressFrame(ui_root)
    delivered = []
    job = frame.after(0, lambda: delivered.append('unexpected'))
    assert job in frame._owned_after
    frame.destroy()
    assert job not in ui_root.tk.call('after', 'info')
    ui_root.update()
    assert delivered == []


def test_segmented_controls_restore_children_after_job(ui_root, monkeypatch):
    from app.ui.frames.convert.frame import ConvertFrame
    from app.ui.operations import operations
    frame = ConvertFrame(ui_root)
    buttons = frame._seg_formato.winfo_children()
    before = [button.cget('state') for button in buttons]
    monkeypatch.setattr('app.ui.operations.Thread.start', lambda thread: thread.run())
    assert frame._submit_job(lambda: {})
    assert all(button.cget('state') == 'disabled' for button in buttons)
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    assert [button.cget('state') for button in buttons] == before
    frame.destroy()


@pytest.mark.parametrize('key', ['convert', 'compress', 'resize', 'remove_bg', 'palette', 'watermark', 'rename', 'ocr', 'metadata', 'lqip'])
@pytest.mark.parametrize('outcome', ['success', 'worker-error', 'start-error'])
def test_each_module_restores_real_controls_after_job(ui_root, monkeypatch, key, outcome):
    import customtkinter as ctk
    from tkinter import Text
    from app.ui.module_registry import get_module_spec, load_frame_class
    from app.ui.frames.ocr.frame import OcrFrame
    from app.ui.frames.remove_bg.frame import RemoveBgFrame
    from app.ui.operations import operations
    monkeypatch.setattr(OcrFrame, '_inicializar_en_background', lambda self: None)
    monkeypatch.setattr(RemoveBgFrame, '_inicializar_en_background', lambda self: self._build_content_ready(True, True))
    frame = load_frame_class(get_module_spec(key))(ui_root)
    ui_root.update()
    states = []
    def capture(parent):
        for widget in parent.winfo_children():
            if isinstance(widget, (ctk.CTkButton, ctk.CTkEntry, ctk.CTkComboBox,
                                   ctk.CTkOptionMenu, ctk.CTkCheckBox, ctk.CTkSlider, Text, ctk.CTkSwitch)):
                states.append((widget, widget.cget('state')))
            else:
                capture(widget)
    capture(frame)
    def fail():
        raise OSError('simulated failure')
    monkeypatch.setattr('app.ui.operations.Thread.start', lambda thread: fail() if outcome == 'start-error' else thread.run())
    accepted = frame._submit_job(fail if outcome == 'worker-error' else lambda: {})
    assert accepted == (outcome != 'start-error')
    if accepted:
        assert all(widget.cget('state') == 'disabled' for widget, _ in states)
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    assert all(widget.cget('state') == original for widget, original in states)
    assert not operations.is_busy()
    frame.destroy()
