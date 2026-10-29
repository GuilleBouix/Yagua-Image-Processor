"""Roles visuales compartidos y comportamiento de los módulos de la interfaz."""
from time import monotonic, sleep

import customtkinter as ctk
from PIL import Image
import pytest

from app.ui import colors, fonts, styles
from app.ui.frames.convert.frame import ConvertFrame
from app.ui.frames.compress.frame import CompressFrame
from app.ui.operations import operations
from app.ui.styles import Button, OptionField
from app.translations import t


@pytest.fixture(autouse=True)
def default_theme(ui_root):
    if fonts.FUENTE_BASE is None:
        fonts.inicializar_fuentes()
    previous = colors.get_current_theme()
    colors.apply_theme('Default')
    yield
    colors.apply_theme(previous)


@pytest.mark.parametrize('event_args', [(), (None,)])
def test_switch_callbacks_accept_optional_event_without_changing_actions(
        ui_root, monkeypatch, event_args):
    callbacks, actions = {}, []
    original_bind = styles.Switch.bind

    def capture_bind(self, sequence, command, add=True):
        callbacks[sequence] = command
        return original_bind(self, sequence, command, add=add)

    monkeypatch.setattr(styles.Switch, 'bind', capture_bind)
    switch = styles.Switch(ui_root, text='Test', command=lambda: actions.append(switch.get()))
    try:
        callbacks['<FocusIn>'](*event_args)
        assert switch._design_focus is True
        callbacks['<FocusOut>'](*event_args)
        assert switch._design_focus is False
        assert actions == []
        callbacks['<Return>'](*event_args)
        callbacks['<space>'](*event_args)
        assert actions == [1, 0]
        switch.configure(state='disabled')
        callbacks['<Return>'](*event_args)
        callbacks['<space>'](*event_args)
        assert actions == [1, 0]
    finally:
        switch.destroy()


@pytest.mark.parametrize('event_args', [(), (None,)])
def test_entry_focus_and_hover_accept_optional_event(ui_root, monkeypatch, event_args):
    callbacks = {}
    original_bind = styles.Entry.bind

    def capture_bind(self, sequence, command, add=True):
        callbacks[sequence] = command
        return original_bind(self, sequence, command, add=add)

    monkeypatch.setattr(styles.Entry, 'bind', capture_bind)
    entry = styles.Entry(ui_root)
    try:
        for enter, leave, flag in [('<Enter>', '<Leave>', '_design_hover'),
                                   ('<FocusIn>', '<FocusOut>', '_design_focus')]:
            callbacks[enter](*event_args)
            assert getattr(entry, flag) is True
            callbacks[leave](*event_args)
            assert getattr(entry, flag) is False
    finally:
        entry.destroy()


def pump(root, condition, timeout=15):
    # Estas pruebas validan flujos completos, no un límite de cinco segundos.
    # Preflight, E/S atómica y callbacks Tk comparten CPU con toda la matriz de interfaz.
    end = monotonic() + timeout
    while monotonic() < end and not condition():
        operations.drain(lambda owner: bool(owner.winfo_exists()))
        root.update()
        sleep(.003)
    assert condition()


def test_default_roles_fonts_and_shared_controls(ui_root):
    frame = ConvertFrame(ui_root)
    p = styles.palette()
    assert p.border == '#3A3A3C'
    assert p.primary_text == '#0A0A0B'
    assert frame._panel_opciones.cget('fg_color') == '#1C1C1E'
    assert frame._lista_frame.cget('fg_color') == '#0F0F11'
    assert frame._btn_convertir.cget('fg_color') == '#FFFFFF'
    assert frame._btn_convertir.cget('hover_color') == '#D1D1D6'
    for button in (frame._btn_seleccionar, frame._btn_limpiar):
        assert button.cget('fg_color') == p.background
        assert button.cget('border_color') == p.border
        assert button.cget('text_color') == p.text
    for widget in (frame._btn_limpiar, frame._btn_seleccionar, frame._btn_convertir,
                   frame._lista_frame, frame._panel_opciones, frame._seg_formato):
        assert widget.cget('corner_radius') == 0
    assert frame._btn_convertir.cget('height') == 40
    assert frame._btn_seleccionar.cget('height') == 40
    assert frame._btn_limpiar.cget('height') == 30
    assert frame._btn_convertir.cget('font') is fonts.FUENTE_BASE
    assert frame._btn_seleccionar.cget('font') is fonts.FUENTE_BASE
    assert frame._btn_limpiar.cget('font') is fonts.FUENTE_CHICA
    assert frame._seg_formato.cget('font') is fonts.FUENTE_CHICA
    menu = next(w for w in frame._save_groups[0].winfo_children() if isinstance(w, OptionField))
    assert menu.menu.cget('font') is fonts.FUENTE_BASE
    assert menu.menu.cget('button_color') == p.inset
    assert menu.menu.cget('corner_radius') == 0
    frame._ensure_full_overlay()
    assert frame._full_overlay_card.cget('corner_radius') == 0
    assert frame._full_overlay_card.cget('border_color') == p.border
    assert frame._full_overlay_bar.cget('corner_radius') == 0


@pytest.mark.parametrize('view_class', [ConvertFrame, CompressFrame])
@pytest.mark.parametrize('theme', colors.get_theme_names())
def test_other_palettes_preserved_with_common_patterns(ui_root, theme, view_class):
    colors.apply_theme(theme)
    before = dict(colors.THEMES[theme])
    frame = view_class(ui_root)
    p = styles.palette()
    primary = getattr(frame, '_btn_convertir', None) or frame._btn_comprimir
    assert primary.cget('fg_color') == before['ACENTO']
    assert frame._panel_opciones.cget('fg_color') == before['PANEL_BG']
    assert frame._lista_frame.cget('fg_color') == before['DROPZONE_BG']
    assert frame._btn_limpiar.cget('text_color') == p.text
    assert styles.contrast(p.primary, p.primary_text) >= 4.5
    assert styles.contrast(p.primary_hover, p.primary_text) >= 4.5
    assert colors.THEMES[theme] == before
    assert colors.SIDEBAR_SEPARATOR == before['SIDEBAR_SEPARATOR']


def test_resize_uses_the_same_shared_styles(ui_root):
    from app.ui.frames.resize.frame import ResizeFrame
    frame = ResizeFrame(ui_root)
    assert frame.design_system
    assert isinstance(frame._btn_limpiar, Button)
    assert frame._btn_limpiar.cget('corner_radius') == 0
    assert frame._btn_limpiar.cget('fg_color') == styles.palette().background
    assert frame._lista_frame.cget('corner_radius') == 0
    assert frame._lista_frame.cget('fg_color') == styles.palette().inset
    assert any(isinstance(w, OptionField) for w in frame._save_groups[0].winfo_children())


@pytest.mark.parametrize('role', ['primary', 'secondary'])
def test_button_states_restore_without_geometry_changes(ui_root, role):
    button = Button(ui_root, role=role, text='Acción', font=fonts.FUENTE_BASE)
    button.pack()
    ui_root.update_idletasks()
    p = styles.palette()
    size = (button.winfo_width(), button.winfo_height())
    button._on_enter()
    if role == 'secondary':
        assert button.cget('border_color') == p.hover_border
    button._set_focus(True)
    assert button.cget('border_color') == (p.primary_text if role == 'primary' else p.text)
    button.configure(state='disabled')
    button._on_enter()
    assert not button.cget('hover')
    assert button.cget('fg_color') == p.disabled
    assert button.cget('border_color') == p.border
    button.configure(state='normal')
    button._set_focus(False)
    button._on_leave()
    ui_root.update_idletasks()
    assert button.cget('fg_color') == (p.primary if role == 'primary' else p.background)
    assert (button.winfo_width(), button.winfo_height()) == size


def test_upload_icon_dims_without_disappearing(ui_root):
    frame = ConvertFrame(ui_root)
    button = frame._btn_seleccionar
    original = button.cget('image')
    button.configure(state='disabled')
    assert isinstance(button.cget('image'), ctk.CTkImage)
    assert button.cget('image') is not original
    assert button.cget('image').cget('size') == original.cget('size')
    button.configure(state='normal')
    assert button.cget('image') is original


def test_segments_variable_click_and_quality_restore(ui_root):
    frame = ConvertFrame(ui_root)
    p = styles.palette()
    for value in ('PNG', 'WEBP', 'JPEG'):
        frame._state.fmt_destino.set(value)
        frame._actualizar_info()
        for name, button in frame._seg_formato._buttons_dict.items():
            assert button.cget('text_color') == (p.primary_text if name == value else p.text)
        selected = frame._seg_formato._buttons_dict[value]
        selected.configure(state='disabled')
        assert selected.cget('fg_color') == p.disabled
        selected.configure(state='normal')
        assert selected.cget('fg_color') == p.primary
        assert frame._slider.cget('state') == ('disabled' if value == 'PNG' else 'normal')
    frame._seg_formato._buttons_dict['PNG'].invoke()
    assert frame._state.fmt_destino.get() == 'PNG'
    assert frame._slider.cget('state') == 'disabled'


def test_keyboard_activation_and_disabled_button(ui_root):
    calls = []
    button = Button(ui_root, text='Acción', command=lambda: calls.append(True))
    button.pack()
    ui_root.deiconify()
    ui_root.update()
    button._canvas.focus_force()
    ui_root.update()
    button._canvas.event_generate('<KeyPress-Return>')
    ui_root.update()
    assert calls == [True]
    button.configure(state='disabled')
    button._canvas.event_generate('<KeyPress-Return>')
    ui_root.update()
    assert calls == [True]


def test_option_menu_keyboard_focus_and_disabled_states(ui_root, monkeypatch):
    field = OptionField(ui_root, values=['Crear copias', 'Sobrescribir originales'])
    field.pack()
    ui_root.deiconify()
    ui_root.update()
    opened = []
    monkeypatch.setattr(field.menu, '_open_dropdown_menu', lambda: opened.append(True))
    field.menu._canvas.focus_force()
    ui_root.update()
    assert field.cget('fg_color') == styles.palette().text
    field.menu._canvas.event_generate('<KeyPress-Return>')
    ui_root.update()
    assert opened == [True]
    field.menu.configure(state='disabled')
    field.menu._canvas.event_generate('<KeyPress-Return>')
    ui_root.update()
    assert opened == [True]
    assert field.cget('fg_color') == styles.palette().border
    field.menu.configure(state='normal')
    field.menu.set('Sobrescribir originales')
    assert field.menu.get() == 'Sobrescribir originales'


@pytest.mark.parametrize('view_class', [ConvertFrame, CompressFrame])
@pytest.mark.parametrize('outcome', ['success', 'worker-error', 'start-error'])
def test_processing_restores_visual_roles(ui_root, monkeypatch, outcome, view_class):
    frame = view_class(ui_root)
    primary = getattr(frame, '_btn_convertir', None) or frame._btn_comprimir
    def fail():
        raise OSError('test')
    monkeypatch.setattr('app.ui.operations.Thread.start',
                        lambda thread: fail() if outcome == 'start-error' else thread.run())
    accepted = frame._submit_job(fail if outcome == 'worker-error' else lambda: {}, on_error=lambda error: None)
    assert accepted == (outcome != 'start-error')
    if accepted:
        assert primary.cget('fg_color') == styles.palette().disabled
        if isinstance(frame, ConvertFrame):
            assert all(b.cget('fg_color') == styles.palette().disabled for b in frame._seg_formato._buttons_dict.values())
        else:
            assert frame._slider.cget('state') == 'disabled'
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    assert not operations.is_busy()
    assert primary.cget('fg_color') == styles.palette().primary
    assert frame._btn_limpiar.cget('fg_color') == styles.palette().background
    if isinstance(frame, ConvertFrame):
        assert frame._seg_formato._buttons_dict['WEBP'].cget('fg_color') == styles.palette().primary
    else:
        assert frame._slider.cget('state') == 'normal'


@pytest.mark.parametrize('view_class', [ConvertFrame, CompressFrame])
def test_virtual_rows_keep_style_and_reuse_on_reload(ui_root, tmp_path, view_class):
    ui_root.geometry('900x600')
    ui_root.deiconify()
    frame = view_class(ui_root)
    frame.pack(fill='both', expand=True)
    source = tmp_path / 'foto.jpg'
    Image.new('RGB', (32, 24)).save(source)
    frame._cargar_imagenes([str(source)] * 100)
    listing = frame._virtual_file_list
    pump(ui_root, lambda: bool(listing.virtual.rows))
    row = next(iter(listing.virtual.rows.values()))
    assert len(listing.virtual.rows) < 100
    assert row.cget('corner_radius') == 0
    assert row.cget('fg_color') == styles.palette().panel
    assert row.cget('border_color') == styles.palette().border
    frame._limpiar()
    frame._cargar_imagenes([str(source)])
    pump(ui_root, lambda: bool(listing.virtual.rows))
    assert frame._virtual_file_list is listing


@pytest.mark.parametrize('overwrite,target', [(False, 'WEBP'), (True, 'JPEG'), (True, 'WEBP')])
def test_convert_real_save_flow(ui_root, tmp_path, monkeypatch, overwrite, target):
    source = tmp_path / 'cámara.jpeg'
    Image.effect_noise((96, 64), 70).convert('RGB').save(source, quality=100)
    original = source.read_bytes()
    folder = tmp_path / 'copias'
    folder.mkdir()
    frame = ConvertFrame(ui_root)
    frame._cargar_imagenes([str(source)])
    frame._state.fmt_destino.set(target)
    frame._state.calidad.set(20)
    frame._save_choice.set(t('save_overwrite' if overwrite else 'save_copies'))
    monkeypatch.setattr('app.ui.saving.filedialog.askdirectory', lambda **kwargs: str(folder))
    monkeypatch.setattr('app.ui.saving.messagebox.askyesno', lambda *args, **kwargs: True)
    frame._convertir()
    pump(ui_root, lambda: hasattr(frame, '_last_save_result') and not operations.is_busy())
    assert frame._last_save_result['ok'] == 1
    if overwrite and target == 'JPEG':
        assert source.read_bytes() != original
    else:
        assert source.read_bytes() == original
        destination = (tmp_path if overwrite else folder) / 'cámara.webp'
        assert destination.is_file()


def test_compress_uses_same_roles_fonts_and_controls(ui_root):
    convert = ConvertFrame(ui_root)
    compress = CompressFrame(ui_root)
    for name in ('_btn_limpiar', '_btn_seleccionar', '_panel_opciones', '_lista_frame'):
        first, second = getattr(convert, name), getattr(compress, name)
        for token in ('corner_radius', 'fg_color'):
            assert first.cget(token) == second.cget(token)
    assert compress._btn_comprimir.cget('font') is fonts.FUENTE_BASE
    assert compress._btn_comprimir.cget('height') == 40
    assert compress._btn_comprimir.cget('fg_color') == convert._btn_convertir.cget('fg_color')
    assert compress._slider.cget('fg_color') == convert._slider.cget('fg_color')
    assert any(isinstance(w, OptionField) for w in compress._save_groups[0].winfo_children())


def test_switch_states_keep_contrast_variable_and_geometry(ui_root):
    selected = ctk.BooleanVar(value=True)
    switch = styles.Switch(ui_root, text='', variable=selected, onvalue=True, offvalue=False)
    switch.pack()
    p = styles.palette()
    ui_root.update_idletasks()
    size = (switch.winfo_reqwidth(), switch.winfo_reqheight())
    assert selected.get() is True
    assert styles.contrast(switch.cget('button_color'), switch.cget('progress_color')) >= 4.5
    switch.toggle()
    assert selected.get() is False
    assert switch.cget('button_color') == p.muted
    selected.set(True)
    assert switch.get() is True
    assert switch.cget('button_color') == '#FFFFFF'
    switch.configure(state='disabled')
    switch.toggle()
    assert selected.get() is True
    assert switch.cget('button_color') == p.muted
    switch.configure(state='normal')
    switch._set_focus(True)
    assert switch.cget('border_color') == p.text
    switch._set_focus(False)
    switch._on_enter()
    assert switch.cget('border_color') == p.hover_border
    switch._on_leave()
    ui_root.update_idletasks()
    assert size == (switch.winfo_reqwidth(), switch.winfo_reqheight())


@pytest.mark.parametrize('scale', [1, .75, .5])
def test_format_padding_and_fit_in_small_real_workspace(ui_root, scale):
    from app.ui.main_window import MainWindow
    previous = ctk.ScalingTracker.widget_scaling
    try:
        ctk.set_widget_scaling(scale)
        ui_root.deiconify()
        ui_root.state('normal')
        ui_root.geometry('900x600')
        window = MainWindow(ui_root, auto_updates=False)
        window.pack(fill='both', expand=True)
        window.show_module('convert')
        frame = window.frames['convert']
        ui_root.update()
        segments = frame._seg_formato
        panel = frame._panel_opciones
        pump(ui_root, lambda: panel.winfo_width() > 400 * scale and
             segments.winfo_rootx() + segments.winfo_width() <= panel.winfo_rootx() + panel.winfo_width())
        for button in frame._seg_formato._buttons_dict.values():
            assert button.cget('font') is fonts.FUENTE_CHICA
            label = button._text_label
            left = label.winfo_rootx() - button.winfo_rootx()
            right = button.winfo_rootx() + button.winfo_width() - label.winfo_rootx() - label.winfo_width()
            assert min(left, right) >= round(8 * scale) - 1
        assert segments.winfo_rootx() + segments.winfo_width() <= panel.winfo_rootx() + panel.winfo_width()
    finally:
        ctk.set_widget_scaling(previous)


@pytest.mark.parametrize('overwrite', [False, True])
def test_compress_real_save_retains_exif(ui_root, tmp_path, monkeypatch, overwrite):
    import piexif
    source = tmp_path / 'cámara.jpeg'
    Image.effect_noise((96, 64), 70).convert('RGB').save(source, quality=100,
        exif=piexif.dump({'0th': {piexif.ImageIFD.Artist: b'Yagua'}}))
    before = source.read_bytes()
    folder = tmp_path / 'copias'
    folder.mkdir()
    frame = CompressFrame(ui_root)
    frame._cargar_imagenes([str(source)])
    frame._state.calidad.set(20)
    frame._save_choice.set(t('save_overwrite' if overwrite else 'save_copies'))
    monkeypatch.setattr('app.ui.saving.filedialog.askdirectory', lambda **kwargs: str(folder))
    monkeypatch.setattr('app.ui.saving.messagebox.askyesno', lambda *args, **kwargs: True)
    frame._comprimir()
    try:
        pump(ui_root, lambda: hasattr(frame, '_last_save_result') and not operations.is_busy())
    except AssertionError:
        pytest.fail(f"Compression did not finish: status={frame._lbl_info.cget('text')!r}, "
                    f"active={operations.active!r}, result={getattr(frame, '_last_save_result', None)!r}")
    assert frame._last_save_result['ok'] == 1
    destination = source if overwrite else folder / source.name
    assert destination.is_file()
    assert destination.stat().st_size < len(before)
    assert piexif.load(str(destination))['0th'].get(piexif.ImageIFD.Artist) == b'Yagua'
    assert source.read_bytes() != before if overwrite else source.read_bytes() == before


def test_compress_without_improvement_creates_no_copy(ui_root, tmp_path, monkeypatch):
    source = tmp_path / 'foto.webp'
    Image.effect_noise((128, 96), 70).convert('RGB').save(source, quality=10)
    before = source.read_bytes()
    folder = tmp_path / 'copias'
    folder.mkdir()
    frame = CompressFrame(ui_root)
    frame._cargar_imagenes([str(source)])
    frame._state.calidad.set(100)
    monkeypatch.setattr('app.ui.saving.filedialog.askdirectory', lambda **kwargs: str(folder))
    monkeypatch.setattr('app.ui.saving.messagebox.askyesno', lambda *args, **kwargs: True)
    frame._comprimir()
    pump(ui_root, lambda: hasattr(frame, '_last_save_result') and not operations.is_busy())
    assert frame._last_save_result['sin_mejora'] == 1
    assert frame._last_save_result['errores'] == 0
    assert source.read_bytes() == before
    assert not list(folder.iterdir())
