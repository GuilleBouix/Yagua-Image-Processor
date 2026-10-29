"""Processing controls keep their state and use immutable batch snapshots."""
from PIL import Image
import pytest

from app.modules.remove_bg import RemoveBgConfig
from app.translations import t
from app.ui.frames.remove_bg.frame import RemoveBgFrame


@pytest.fixture
def view(monkeypatch, ui_root):
    monkeypatch.setattr(RemoveBgFrame, '_inicializar_en_background',
                        lambda self: self._build_content_ready(True, True))
    frame = RemoveBgFrame(ui_root)
    frame.pack(fill='both', expand=True)
    ui_root.update()
    return frame


def test_defaults_and_visible_edge_controls(view):
    assert view._processing_config() == RemoveBgConfig()
    assert view._edge_controls.winfo_manager() == 'grid'
    assert not hasattr(view, '_btn_advanced')
    assert not hasattr(view, '_output_background')
    view._halo_changed(40)
    view._contour_changed(-2)
    assert view._lbl_halo.cget('text') == '40%'
    assert view._lbl_contour.cget('text') == '-2 px'
    assert view._processing_config().halo_strength == 40
    assert view._processing_config().edge_offset == -2


def test_batch_captures_settings_before_confirmation(view, tmp_path, monkeypatch):
    source = tmp_path / 'foto.png'
    Image.new('RGB', (20, 20), 'red').save(source)
    view._cargar_imagenes([str(source)])
    view._refine_edges.set(t('remove_bg_off'))
    view._halo_changed(0)
    snapshot = view._processing_config()
    callbacks, processed = [], []
    monkeypatch.setattr(view, '_prepare_save', lambda paths, fmt, proceed: callbacks.append(proceed))
    monkeypatch.setattr(view, '_proceso', lambda *args, **kwargs: processed.append(kwargs['config']))
    monkeypatch.setattr(view, '_submit_job', lambda work, **kwargs: work())
    view._procesar()
    view._refine_edges.set(t('remove_bg_on'))
    view._halo_changed(100)
    callbacks[0](str(tmp_path), object())
    assert processed == [snapshot]
    assert processed[0].refine_edges == 'off'


def test_settings_change_keeps_saved_preview_and_explains_reprocessing(view, tmp_path):
    output = str(tmp_path / 'saved.png')
    view._preview_outputs['source'] = output
    previous = view._preview.path
    view._contour_changed(1)
    assert view._preview.path == previous
    assert view._lbl_info.cget('text') == t('remove_bg_apply_hint')
