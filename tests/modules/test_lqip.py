import html
import os
import re
from pathlib import Path

from app.modules.lqip import batch_procesar


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
