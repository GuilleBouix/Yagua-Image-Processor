"""Regresiones de integración para el rediseño aprobado de la aplicación de escritorio."""
from pathlib import Path
from time import monotonic, sleep

import customtkinter as ctk
from PIL import Image
import pytest

from app.translations import t
from app.ui import colors, fonts, styles
from app.ui.frames.metadata.frame import MetadataFrame
from app.ui.frames.ocr.frame import OcrFrame
from app.ui.frames.remove_bg.frame import RemoveBgFrame
from app.ui.module_registry import iter_all_modules, load_frame_class
from app.ui.operations import operations


def pump(root, condition=lambda: False, timeout=.2):
    deadline = monotonic() + timeout
    while monotonic() < deadline and not condition():
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        root.update()
        sleep(.003)


def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)


@pytest.fixture(autouse=True)
def isolate(ui_root, monkeypatch):
    if fonts.FUENTE_BASE is None:
        fonts.inicializar_fuentes()
    previous = colors.get_current_theme()
    tracker = ctk.ScalingTracker
    callbacks = {window: list(items) for window, items in tracker.window_widgets_dict.items()}
    dpi_scaling = dict(tracker.window_dpi_scaling_dict)
    old_scale = tracker.widget_scaling
    errors = []
    monkeypatch.setattr(ui_root._root(), 'report_callback_exception',
        lambda kind, error, traceback: errors.append(f'{kind.__name__}: {error}'))
    monkeypatch.setattr(OcrFrame, '_inicializar_en_background', lambda self: None)
    monkeypatch.setattr(RemoveBgFrame, '_inicializar_en_background',
        lambda self: self._build_content_ready(True, True))
    colors.apply_theme('Default')
    yield
    # Destruye ventanas y widgets de prueba antes de restaurar la escala global. Un
    # CTkToplevel puede seguir construyéndose mientras corren callbacks de escala
    # en Windows y dejar una instancia parcial en el registro al limpiar.
    for child in ui_root.winfo_children():
        child.destroy()
    tracker.window_widgets_dict = callbacks
    tracker.window_dpi_scaling_dict = dpi_scaling
    # Las ventanas de esta fixture se descartan; actualiza el factor global sin
    # invoking callbacks on stale or partially initialized CTkToplevel objects.
    tracker.widget_scaling = old_scale
    colors.apply_theme(previous)
    assert not errors, errors


@pytest.mark.parametrize('theme', colors.get_theme_names())
def test_all_modules_share_roles_and_restore_controls(ui_root, theme):
    colors.apply_theme(theme)
    p = styles.palette()
    for spec in iter_all_modules():
        if not spec.enabled:
            continue
        view = load_frame_class(spec)(ui_root)
        view.pack(fill='both', expand=True)
        ui_root.update()
        assert view.design_system, spec.key
        assert view._scrollbar.cget('corner_radius') == 0
        for widget in descendants(view):
            if isinstance(widget, styles.Button):
                assert widget.cget('corner_radius') == 0, spec.key
                before = (widget.cget('fg_color'), widget.cget('font'), widget.cget('height'))
                state = widget.cget('state')
                widget.configure(state='disabled')
                widget._on_enter()
                assert widget.cget('fg_color') == p.disabled
                assert not widget.cget('hover')
                widget.configure(state=state)
                widget._on_leave()
                assert before == (widget.cget('fg_color'), widget.cget('font'), widget.cget('height'))
            elif isinstance(widget, (styles.Entry, styles.ComboBox, styles.CheckBox)):
                assert widget.cget('corner_radius') == 0, spec.key
        view.destroy()


def load_metadata(view, monkeypatch, paths):
    from app.modules.metadata_batch import leer_archivo
    from app.ui.frames.metadata.collection import decode_preview
    controller = view._collection
    def enqueue(kind, key):
        if kind == 'active':
            controller.loaded(controller.epoch, controller.revision, key,
                (leer_archivo(key), '', decode_preview(key), ''))
    monkeypatch.setattr(controller, 'enqueue', enqueue)
    view._cargar_lote(paths)


def picture(tmp_path, name='foto.jpg', size=(160, 100)):
    path = tmp_path / name
    Image.new('RGB', size, 'teal').save(path)
    return str(path)


@pytest.mark.parametrize('dialog_kind', ['save', 'copy'])
def test_metadata_dialogs_styles_search_scope_and_cancel(ui_root, monkeypatch, tmp_path, dialog_kind):
    view = MetadataFrame(ui_root)
    view.pack(fill='both', expand=True)
    ui_root.deiconify()
    paths = [picture(tmp_path), picture(tmp_path, 'otra.jpg')]
    before = [Path(path).read_bytes() for path in paths]
    load_metadata(view, monkeypatch, paths)
    view._campos_edit['Artist'].insert(0, 'Guille')
    view._collection.capture()
    monkeypatch.setattr('app.ui.frames.metadata.collection.filedialog.askdirectory', lambda **kwargs: '')
    inspected, failures = [], []
    def inspect():
        dialog = next((widget for widget in descendants(view) if isinstance(widget, ctk.CTkToplevel)), None)
        widgets = list(descendants(dialog)) if dialog is not None else []
        buttons = [widget for widget in widgets if isinstance(widget, ctk.CTkButton)]
        # CTkToplevel performs an update during its constructor on Windows.
        # Wait for both actions, rather than inspecting/destroying a partial window.
        if dialog is None or not any(button.cget('text') == t('meta_cancel') for button in buttons):
            view.after(30, inspect)
            return
        try:
            assert dialog.cget('fg_color') == styles.palette().background
            assert buttons and all(isinstance(button, styles.Button) for button in buttons)
            assert all(button.cget('corner_radius') == 0 for button in buttons)
            if dialog_kind == 'copy':
                search = next(widget for widget in widgets if isinstance(widget, styles.Entry))
                search.insert(0, 'campo inexistente')
                search.delete(0, 'end')
                checks = [widget for widget in widgets if isinstance(widget, styles.CheckBox)]
                assert checks
                checks[0].toggle()
                checks[0].toggle()
            else:
                radios = [widget for widget in widgets if isinstance(widget, ctk.CTkRadioButton)]
                assert len(radios) == 2
                radios[1].invoke()
                next(button for button in buttons if button.cget('text') == t('meta_continue')).invoke()
                assert dialog.winfo_exists()  # Cancelling the folder picker keeps the dialog open.
            inspected.append(True)
            next(button for button in buttons if button.cget('text') == t('meta_cancel')).invoke()
        except Exception as error:
            failures.append(error)
        finally:
            if dialog.winfo_exists():
                dialog.destroy()
    view.after(60, inspect)
    if dialog_kind == 'copy':
        view._collection.choose_fields()
    else:
        assert view._collection.destination(2, choose_scope=True) is None
    assert not failures, failures
    assert inspected
    assert before == [Path(path).read_bytes() for path in paths]
    assert not view._state.items[next(reversed(view._state.items))].draft.dirty


@pytest.mark.parametrize('scale', [1, .75, .5])
def test_metadata_editor_save_actions_fit_visible_height(ui_root, monkeypatch, tmp_path, scale):
    ctk.set_widget_scaling(scale)
    ui_root.deiconify()
    ui_root.state('normal')
    ui_root.geometry('1100x640')
    pump(ui_root, lambda: ui_root.winfo_width() == 1100 and ui_root.winfo_height() == 640, timeout=3)
    assert (ui_root.winfo_width(), ui_root.winfo_height()) == (1100, 640)
    view = MetadataFrame(ui_root)
    view.pack(fill='both', expand=True)
    load_metadata(view, monkeypatch, [picture(tmp_path)])
    view._tab.set(t('edit'))
    view._cambiar_tab(t('edit'))
    pump(ui_root, timeout=.4)
    button = view._btn_guardar_edit
    assert button.winfo_ismapped()
    assert button.winfo_rooty() + button.winfo_height() <= (
        view._parent_canvas.winfo_rooty() + view._parent_canvas.winfo_height())
    assert view._panel_editar._parent_canvas.winfo_height() > 100 * scale


def test_watermark_preview_after_processing_clear_and_reload(ui_root, monkeypatch, tmp_path):
    from app.ui.frames.watermark.frame import WatermarkFrame
    ui_root.geometry('1100x640')
    ui_root.deiconify()
    view = WatermarkFrame(ui_root)
    view.pack(fill='both', expand=True)
    source = picture(tmp_path)
    stamp = tmp_path / 'marca.png'
    Image.new('RGBA', (20, 20), (240, 30, 30, 160)).save(stamp)
    output = tmp_path / 'copias'
    output.mkdir()
    monkeypatch.setattr('app.ui.saving.filedialog.askdirectory', lambda **kwargs: str(output))
    monkeypatch.setattr('app.ui.saving.messagebox.askyesno', lambda *args, **kwargs: True)
    for iteration in range(2):
        view._cargar_imagenes([source])
        view._state.ruta_watermark.set(str(stamp))
        view._mostrar_watermark_item(str(stamp))
        view._cargar_preview_wm(str(stamp))
        pump(ui_root, lambda: view._canvas_preview.cget('image') is not None, timeout=6)
        assert isinstance(view._canvas_preview.cget('image'), ctk.CTkImage)
        view._ejecutar()
        pump(ui_root, lambda: not operations.is_busy() and hasattr(view, '_last_save_result'), timeout=6)
        assert not operations.is_busy()
        assert view._last_save_result['ok'] == 1
        assert (output / ('foto.jpg' if iteration == 0 else 'foto_1.jpg')).exists()
        view._limpiar()
        assert view._canvas_preview.cget('image') is None
        assert view._canvas_preview._label.cget('image') == ''
        assert view._wm_thumb_label._label.cget('image') == ''


def test_rename_layout_preview_and_real_rename(ui_root, tmp_path):
    from app.ui.frames.rename.frame import RenameFrame
    ui_root.deiconify()
    view = RenameFrame(ui_root)
    view.pack(fill='both', expand=True)
    source = picture(tmp_path)
    view._cargar_imagenes([source])
    view._state.prefijo.set('imagen')
    view._state.numeracion_activa.set(True)
    pump(ui_root, lambda: bool(view._preview_data), timeout=4)
    assert view._preview_data[0][1] == 'imagen_001.jpg'
    destination = tmp_path / view._preview_data[0][1]
    assert view._lista_preview._parent_frame.master is view._workspace_right
    assert view._btn_renombrar.master is view._workspace_left
    view._renombrar()
    pump(ui_root, lambda: not operations.is_busy() and not view._imagenes, timeout=5)
    assert destination.is_file() and not Path(source).exists()


@pytest.mark.parametrize('frame_class', [OcrFrame, RemoveBgFrame])
def test_model_loading_uses_same_square_overlay(ui_root, frame_class):
    view = frame_class(ui_root)
    view.pack(fill='both', expand=True)
    ui_root.deiconify()
    ui_root.update()
    view._show_overlay(t('loading_model'))
    pump(ui_root)
    assert view._full_overlay_card.cget('corner_radius') == 0
    assert view._full_overlay_bar.cget('corner_radius') == 0
    assert view._full_overlay_bar.cget('fg_color') == styles.palette().border
    assert view._full_overlay_bar._loop_running
    view._hide_overlay()
    assert not view._full_overlay_bar._loop_running
    assert not view._full_overlay_frame.winfo_manager()
