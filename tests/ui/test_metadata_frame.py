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
