import customtkinter as ctk

from app.modules.metadata import CAMPOS_EDITABLES, GRUPOS_CAMPOS_EDITABLES
from app.translations import t
from app.ui.frames.metadata.frame import MetadataFrame


def test_metadata_frame_build(ui_root):
    frame = MetadataFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_tab")
    assert hasattr(frame, "_frames")
    assert t("view") in frame._frames
    assert t("edit") in frame._frames
    assert t("clean_batch") in frame._frames

    assert isinstance(frame._campos_edit["ImageDescription"], ctk.CTkEntry)
    assert isinstance(frame._campos_edit["ExposureProgram"], ctk.CTkComboBox)
    assert len(frame._campos_edit) == len(CAMPOS_EDITABLES)
    assert isinstance(frame._panel_editar, ctk.CTkScrollableFrame)
    assert all(
        widget.get() == ""
        for key, widget in frame._campos_edit.items()
        if key not in frame._enum_values
    )
    assert all(
        widget.get() == t("leave_unchanged")
        for key, widget in frame._campos_edit.items()
        if key in frame._enum_values
    )
    assert frame._sync_dates_var.get() is False
    assert frame._clear_gps_var.get() is False
    assert set().union(*GRUPOS_CAMPOS_EDITABLES.values(), {"DateTimeOriginal"}) == set(CAMPOS_EDITABLES)

    frame._aplicar_campos_edit({
        "ImageDescription": "Paisaje",
        "ExposureProgram": "3",
        "GPSLatitude": "-34.6",
        "__image_size__": "640 x 480",
        "__color_space__": "1",
        "__orientation__": "6",
    })
    assert frame._campos_edit["ImageDescription"].get() == "Paisaje"
    assert frame._campos_edit["ExposureProgram"].get() == t("enum_aperture_priority")
    assert frame._campos_edit["GPSLatitude"].get() == "-34.6"
    assert t("color_srgb") in frame._info_tecnica.cget("text")


def test_clear_resets_optional_fields_and_selectors(ui_root):
    frame = MetadataFrame(ui_root)
    frame._aplicar_campos_edit({'Artist': 'Author', 'ExposureProgram': '3'})
    frame._sync_dates_var.set(True)
    frame._clear_gps_var.set(True)
    frame._limpiar()
    assert frame._state.ruta is None
    assert frame._state.ruta_edicion is None
    for widget in frame._campos_edit.values():
        assert widget.get() == (t('leave_unchanged') if isinstance(widget, ctk.CTkComboBox) else '')
    assert not frame._sync_dates_var.get()
    assert not frame._clear_gps_var.get()
    assert frame._combo_orientacion.get() == t('keep_orientation')


def test_unchanged_preloaded_fields_do_not_prompt_overwrite(ui_root, monkeypatch):
    frame = MetadataFrame(ui_root)
    frame._state.ruta_edicion = 'image.jpg'
    frame._aplicar_campos_edit({'Artist': 'Existing', 'GPSLatitude': '-34.6', 'GPSLongitude': '-58.3'})
    def unexpected(*args, **kwargs):
        raise AssertionError('Unchanged fields must not prompt to rewrite')
    monkeypatch.setattr('app.ui.frames.metadata.frame.messagebox.askyesno', unexpected)
    frame._guardar_edicion()
    assert frame._lbl_info.cget('text') == t('no_metadata_changes')


def test_view_selection_does_not_redirect_editor_save(ui_root, monkeypatch, tmp_path):
    from PIL import Image
    from app.ui.operations import operations
    paths = [tmp_path / 'A.jpg', tmp_path / 'B.jpg']
    for path in paths:
        Image.new('RGB', (4, 3)).save(path)
    frame = MetadataFrame(ui_root)
    monkeypatch.setattr('app.ui.operations.Thread.start', lambda thread: thread.run())
    monkeypatch.setattr('app.ui.frames.metadata.frame.filedialog.askopenfilename', lambda **kwargs: str(paths[0]))
    frame._explorar_editar()
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    monkeypatch.setattr('app.ui.frames.metadata.frame.filedialog.askopenfilename', lambda **kwargs: str(paths[1]))
    frame._explorar_ver()
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    frame._campos_edit['Artist'].insert(0, 'Edited A')
    saved = []
    def save(source, destination, request):
        saved.append((source, destination))
        return True, None
    monkeypatch.setattr('app.ui.frames.metadata.frame.editar_exif', save)
    monkeypatch.setattr('app.ui.frames.metadata.frame.messagebox.askyesno', lambda *args, **kwargs: True)
    frame._guardar_edicion()
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    assert saved == [(str(paths[0]), str(paths[0]))]


def test_failed_editor_load_preserves_previous_target_and_fields(ui_root, monkeypatch, tmp_path):
    from app.ui.operations import operations
    frame = MetadataFrame(ui_root)
    frame._state.ruta_edicion = 'previous.jpg'
    frame._aplicar_campos_edit({'Artist': 'Previous'})
    broken = tmp_path / 'broken.jpg'
    broken.write_bytes(b'not an image')
    monkeypatch.setattr('app.ui.frames.metadata.frame.filedialog.askopenfilename', lambda **kwargs: str(broken))
    monkeypatch.setattr('app.ui.operations.Thread.start', lambda thread: thread.run())
    frame._explorar_editar()
    operations.drain(lambda owner: bool(owner.winfo_exists()))
    assert frame._state.ruta_edicion == 'previous.jpg'
    assert frame._campos_edit['Artist'].get() == 'Previous'
    assert not operations.is_busy()


def test_view_only_cannot_be_saved_as_editor_target(ui_root, monkeypatch):
    frame = MetadataFrame(ui_root)
    frame._state.ruta = 'view-only.jpg'
    frame._campos_edit['Artist'].insert(0, 'Author')
    def unexpected(*args, **kwargs):
        raise AssertionError('Viewing must not authorize an editor save')
    monkeypatch.setattr('app.ui.frames.metadata.frame.messagebox.askyesno', unexpected)
    frame._guardar_edicion()
    assert frame._state.ruta_edicion is None


def test_export_failure_reports_error_and_preserves_existing_file(ui_root, monkeypatch, tmp_path):
    frame = MetadataFrame(ui_root)
    frame._state.metadatos = {'Artist': 'Author'}
    target = tmp_path / 'metadata.json'
    target.write_bytes(b'previous')
    monkeypatch.setattr('app.ui.frames.metadata.frame.filedialog.asksaveasfilename', lambda **kwargs: str(target))
    def denied(*args):
        raise PermissionError('simulated write failure')
    monkeypatch.setattr('app.utils.output.os.replace', denied)
    frame._exportar('json')
    assert target.read_bytes() == b'previous'
    assert frame._lbl_info.cget('text') == t('error_saving')
