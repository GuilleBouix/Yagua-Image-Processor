"""Pruebas de interfaz para metadata frame y sus estados principales."""

import customtkinter as ctk
import pytest

from app.modules.metadata import CAMPOS_EDITABLES, GRUPOS_CAMPOS_EDITABLES
from app.translations import t
from app import translations
from app.ui.frames.metadata.frame import MetadataFrame


@pytest.mark.parametrize('language', list(translations.AVAILABLE_LANGUAGES))
def test_metadata_frame_build(ui_root, monkeypatch, language):
    monkeypatch.setattr(translations, '_current_lang', language)
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
    for field, mapping in frame._enum_values.items():
        assert frame._campos_edit[field].cget('values') == [t('leave_unchanged'), *mapping]
        assert len(set(mapping.values())) == len(mapping)
    assert set(frame._orientacion_values.values()) == set(range(1, 9))
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


@pytest.mark.parametrize('language', list(translations.AVAILABLE_LANGUAGES))
def test_clear_resets_optional_fields_and_selectors(ui_root, monkeypatch, language):
    monkeypatch.setattr(translations, '_current_lang', language)
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
