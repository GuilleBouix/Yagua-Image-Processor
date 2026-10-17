"""Presentación del catálogo compartido sin depender del sistema operativo."""
import customtkinter as ctk
import pytest

from app import translations
from app.modules.metadata import CAMPOS_VISIBLES, GRUPOS_CAMPOS_VISIBLES
from app.translations import t
from app.ui.frames.metadata.frame import MetadataFrame


def _datos():
    datos = {etiqueta: '0' for etiqueta, _ in CAMPOS_VISIBLES.values()}
    datos['Descripcion de imagen'] = 'Gato'
    datos['Comentario'] = 'Un gato mirando 👀\n' + 'Comentario largo con acentos. ' * 25
    datos['Software'] = 'Yagua'
    datos['Autor'] = 'Guille'
    datos['Copyright'] = 'CAT'
    datos['__gps_decimal__'] = '0.0,0.0'
    return datos


@pytest.mark.parametrize('language', list(translations.AVAILABLE_LANGUAGES))
def test_secciones_etiquetas_y_contador_en_idiomas_disponibles(ui_root, monkeypatch, language):
    monkeypatch.setattr(translations, '_current_lang', language)
    frame = MetadataFrame(ui_root)
    frame._state.ruta = 'gato.jpg'
    frame._aplicar_metadatos(_datos())
    assert len(frame._metadata_rows) == len(CAMPOS_VISIBLES)
    assert [label.cget('text') for label in frame._metadata_sections] == [
        t(f'metadata_section_{grupo}') for grupo in GRUPOS_CAMPOS_VISIBLES
    ]
    for nombre, label, value in frame._metadata_rows:
        assert label.cget('text') == t(CAMPOS_VISIBLES[nombre][1])
        assert label.cget('text') and not label.cget('text').startswith('metadata_')
        assert value.cget('text')
        assert value.cget('justify') == 'left'
    assert frame._lbl_info.cget('text') == f'{len(CAMPOS_VISIBLES)} {t("fields_found")} - gato.jpg'
    opciones = {nombre: value.cget('text') for nombre, _, value in frame._metadata_rows}
    assert opciones['Flash'] == f'{t("flash_no")} (0)'
    assert opciones['ExposureProgram'] == f'{t("enum_not_defined")} (0)'


def test_solo_muestra_secciones_con_datos_y_limpia(ui_root):
    frame = MetadataFrame(ui_root)
    frame._renderizar_metadatos({'Autor': 'Guille', 'Software': 'Yagua', 'Comentario': ''})
    assert len(frame._metadata_rows) == 2
    assert [label.cget('text') for label in frame._metadata_sections] == [t('metadata_section_description')]
    frame._limpiar_todo()
    assert not frame._metadata_rows and not frame._metadata_sections
    frame._renderizar_metadatos({})
    assert not frame._metadata_rows and not frame._metadata_sections
    assert frame._scroll_meta.winfo_children()[0].cget('text') == t('no_metadata_image')


def test_mapas_solo_en_coordenadas_incluso_cero(ui_root, monkeypatch):
    ui_root.deiconify()
    frame = MetadataFrame(ui_root)
    frame.pack(fill='both', expand=True)
    frame._renderizar_metadatos(_datos())
    ui_root.update()
    opened = []
    monkeypatch.setattr('app.ui.frames.metadata.frame.webbrowser.open', opened.append)
    for nombre, _, value in frame._metadata_rows:
        if nombre in ('GPSLatitude', 'GPSLongitude'):
            assert t('view_on_maps') in value.cget('text')
            value._label.event_generate('<Button-1>')
        else:
            assert t('view_on_maps') not in value.cget('text')
    assert opened == ['https://maps.google.com/?q=0.0,0.0'] * 2


@pytest.mark.parametrize('width,height', [(1360, 720), (900, 600)])
def test_textos_largos_y_columnas_caben_en_el_panel(ui_root, width, height):
    ui_root.geometry(f'{width}x{height}')
    ui_root.deiconify()
    sidebar = ctk.CTkFrame(ui_root, width=240)
    sidebar.pack(side='left', fill='y')
    sidebar.pack_propagate(False)
    frame = MetadataFrame(ui_root)
    frame.pack(side='left', fill='both', expand=True)
    errors = []
    ui_root.report_callback_exception = lambda *args: errors.append(args)
    frame._renderizar_metadatos(_datos())
    ui_root.update()
    table = frame._scroll_meta
    for _, label, value in frame._metadata_rows:
        for widget in (label, value):
            assert widget.winfo_x() >= 0
            assert widget.winfo_x() + widget.winfo_width() <= table.winfo_width() + 1
    comment = next(value for nombre, _, value in frame._metadata_rows if nombre == 'UserComment')
    assert comment.winfo_height() > 36
    assert not errors
