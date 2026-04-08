from app.ui.frames.vectorizar.frame import VectorizarFrame


def test_vectorizar_frame_build(ui_root):
    frame = VectorizarFrame(ui_root)
    ui_root.update_idletasks()

    assert hasattr(frame, "_btn_seleccionar")
    assert hasattr(frame, "_lista_frame")
    assert hasattr(frame, "_combo_preset")
    assert hasattr(frame, "_btn_exportar")
    assert hasattr(frame, "_btn_limpiar_param")


def test_vectorizar_frame_muestra_omitidos_si_todos_son_grandes(tmp_path, ui_root):
    frame = VectorizarFrame(ui_root)
    ui_root.update_idletasks()

    grande = tmp_path / "grande.png"
    grande.write_bytes(b"\x00" * (1_000_000 + 1))

    frame._cargar_imagenes([str(grande)])
    ui_root.update_idletasks()

    txt = frame._lbl_info.cget("text").lower()
    assert "omitid" in txt
    assert "1 mb" in txt
    assert "excedid" in txt
