"""Pruebas de regresión del módulo de procesamiento palette."""

from PIL import Image
from app.modules.palette import extraer_paleta, rgb_a_hex, exportar_paleta_imagen


def test_palette_frequency_and_roundtrip(tmp_path):
    source = tmp_path / 'colors.png'
    image = Image.new('RGB', (4, 1))
    image.putdata([(255, 0, 0)] * 3 + [(0, 0, 255)])
    image.save(source)
    palette = extraer_paleta(source, 2)
    assert palette == [(255, 0, 0), (0, 0, 255)]
    assert rgb_a_hex(palette[0]).lower() == '#ff0000'
    output = tmp_path / 'palette.png'
    exportar_paleta_imagen(palette, output)
    with Image.open(output) as saved:
        assert saved.format == 'PNG'
        assert saved.width > 0 and saved.height > 0
