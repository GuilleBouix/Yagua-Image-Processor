import html
import base64
import json
import os
import re
from pathlib import Path

from app.modules.lqip import batch_procesar
from app.modules.lqip import exportar_json, exportar_txt
from app.ui.frames.lqip.services import cargar_original, procesar_archivos


def test_lqip_batch(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.png"

    res = batch_procesar([str(entrada)], modo="lqip", ancho=16, blur=1.0, calidad_lqip=40)
    assert res["ok"] == 1
    assert res["resultados"]
    assert res["resultados"][0]["data_uri"].startswith("data:image/jpeg;base64,")


def test_lqip_escapa_html_y_sanitiza_css(tmp_path: Path, fixtures_dir: Path):
    origen = fixtures_dir / 'sample.png'
    # Windows no permite comillas dobles en nombres de archivo, pero igual queremos
    # validar escaping HTML + sanitizacion de selector CSS.
    if os.name == "nt":
        entrada = tmp_path / "bad& onerror=alert(1)} body { color: red; }.png"
    else:
        entrada = tmp_path / 'bad" onerror="alert(1)"} body { color: red; }.png'
    entrada.write_bytes(origen.read_bytes())

    res = batch_procesar([str(entrada)], modo='lqip', ancho=16, blur=1.0, calidad_lqip=40)

    assert res['ok'] == 1
    resultado = res['resultados'][0]
    expected_alt = html.escape(Path(entrada).stem, quote=True)
    assert f'alt="{expected_alt}"' in resultado['html_tag']

    selector = resultado['css_bg'].split('{', 1)[0].strip()
    assert re.fullmatch(r'\.[a-z0-9_-]+', selector)


def test_results_keep_source_identity_and_partial_errors(tmp_path, fixtures_dir):
    paths = []
    for directory in ('one', 'two'):
        folder = tmp_path / directory
        folder.mkdir()
        path = folder / 'same.png'
        path.write_bytes((fixtures_dir / 'sample.png').read_bytes())
        paths.append(str(path))
    paths.insert(1, str(tmp_path / 'missing.png'))
    items = procesar_archivos(tuple(paths), dict(
        modo='lqip', ancho=20, blur=2, calidad_lqip=40, calidad_b64=85,
    ))
    assert [item.path for item in items] == paths
    assert [item.index for item in items] == [0, 1, 2]
    assert items[1].error and items[1].result is None
    assert items[0].result['nombre'] == items[2].result['nombre'] == 'same.png'
    for item in (items[0], items[2]):
        assert item.dimensions[0] == 20
        assert item.jpeg_bytes == len(base64.b64decode(item.result['base64']))
        assert item.uri_bytes == len(item.result['data_uri'].encode('utf-8'))


def test_base64_preserves_dimensions_and_exports_raw_string(tmp_path, fixtures_dir):
    path = str(fixtures_dir / 'sample.png')
    source = cargar_original(0, path)
    item = procesar_archivos((path,), dict(
        modo='base64', ancho=20, blur=2, calidad_lqip=40, calidad_b64=85,
    ))[0]
    assert item.dimensions == source.dimensions
    assert source.size == Path(path).stat().st_size
    assert not item.result['base64'].startswith('data:')
    txt = tmp_path / 'output.txt'
    json_path = tmp_path / 'output.json'
    exportar_txt([item.result], txt, campo='base64')
    exportar_json([item.result], json_path)
    assert item.result['base64'] in txt.read_text(encoding='utf-8')
    result = json.loads(json_path.read_text(encoding='utf-8'))[0]
    assert set(result) == {'nombre', 'base64', 'data_uri', 'html_tag', 'css_bg'}
    assert result['base64'] == item.result['base64']
