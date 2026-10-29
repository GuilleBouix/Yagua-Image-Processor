"""Selector nativo, modos de Canvas y confirmación de PNG por archivo."""
from pathlib import Path

import pytest
from PIL import Image

from app.translations import t
from app.ui.frames.resize.frame import ResizeFrame
from tests.ui.test_saving import synchronous


def test_canvas_color_picker_cancel_and_transparent_preserve_choice(ui_root, monkeypatch):
    view = ResizeFrame(ui_root)
    assert view._canvas_background() == (255, 255, 255)
    assert view._state.color_fondo.get() == t('canvas_color')
    choices = iter([((10, 80, 192), '#0a50c0'), (None, None)])
    monkeypatch.setattr('app.ui.frames.resize.frame.colorchooser.askcolor', lambda **kwargs: next(choices))
    view._choose_canvas_color()
    assert view._canvas_background() == (10, 80, 192)
    assert view._canvas_color_swatch.cget('fg_color') == '#0A50C0'
    view._choose_canvas_color()
    assert view._state.canvas_color.get() == '#0A50C0'
    view._state.color_fondo.set(t('transparent'))
    assert view._canvas_background() is None
    assert view._canvas_color_button.cget('state') == 'disabled'
    view._state.color_fondo.set(t('canvas_color'))
    assert view._canvas_background() == (10, 80, 192)
    assert view._canvas_color_button.cget('state') == 'normal'


@pytest.mark.parametrize('mode', ['copies', 'overwrite'])
@pytest.mark.parametrize('accept', [False, True])
def test_canvas_png_confirmation_and_safe_destinations(ui_root, tmp_path, monkeypatch, mode, accept):
    view = ResizeFrame(ui_root)
    synchronous(view, monkeypatch)
    jpeg, png = tmp_path / 'cámara.jpeg', tmp_path / 'transparente.png'
    Image.new('RGB', (4, 4), 'red').save(jpeg)
    Image.new('RGBA', (4, 4), (20, 80, 200, 128)).save(png)
    originals = {p: p.read_bytes() for p in (jpeg, png)}
    view._cargar_imagenes([str(jpeg), str(png)])
    view._state.color_fondo.set(t('transparent'))
    view._state.canvas_width_var.set('8')
    view._state.canvas_height_var.set('8')
    view._save_choice.set(t('save_copies' if mode == 'copies' else 'save_overwrite'))
    folder = tmp_path / 'out'
    folder.mkdir()
    monkeypatch.setattr('app.ui.saving.filedialog.askdirectory', lambda **kwargs: str(folder))
    confirmations = []
    def confirm(title, text, **kwargs):
        confirmations.append(text)
        return accept
    monkeypatch.setattr('app.ui.saving.messagebox.askyesno', confirm)
    view._ejecutar_canvas()
    assert t('canvas_png_notice').format(count=1) in confirmations[0]
    assert t('save_confirm').format(replace=0 if mode == 'copies' else 1,
                                   copies=2 if mode == 'copies' else 1) in confirmations[0]
    assert jpeg.read_bytes() == originals[jpeg]
    if not accept:
        assert png.read_bytes() == originals[png]
        assert list(folder.iterdir()) == []
        assert not jpeg.with_suffix('.png').exists()
    else:
        result = view._last_save_result
        assert (result['ok'], result['errores']) == (2, 0)
        for row in result['items']:
            with Image.open(row['destino']) as output:
                assert output.size == (8, 8)
                assert output.convert('RGBA').getpixel((0, 0))[3] == 0
            assert Path(row['destino']).parent == (folder if mode == 'copies' else tmp_path)


def test_canvas_overwrite_refreshes_original_dimensions(ui_root, tmp_path):
    from app.modules.resize import batch_canvas
    from tests.ui.test_live_previews import pump
    source = tmp_path / 'source.png'
    Image.new('RGB', (4, 4), 'red').save(source)
    view = ResizeFrame(ui_root)
    view._cargar_imagenes([str(source)])
    pump(ui_root, lambda: view._crop_source_dimensions == dict(width=4, height=4))
    result = batch_canvas([str(source)], None, ancho=8, alto=8, color_fondo=None,
                          output_policy='overwrite')
    view._finish_save(result)
    pump(ui_root, lambda: view._crop_source_dimensions == dict(width=8, height=8))
    assert view._state.crop_width_var.get() == '8'
