"""
Módulo de extracción de paleta de colores.
"""

from pathlib import Path
from PIL import Image


def cargar_preview(ruta: str, size: tuple[int, int] = (80, 80)) -> tuple[Image.Image, int, int, str]:
    """Carga imagen, genera preview y devuelve metadata básica."""
    with Image.open(ruta) as img:
        w, h = img.size
        img = img.convert('RGB')
        img.thumbnail(size, Image.Resampling.LANCZOS)
        preview = img.copy()
    ext = Path(ruta).suffix.upper().lstrip(".")
    return preview, w, h, ext


def extraer_paleta(ruta: str, n_colores: int = 6) -> list[tuple[int, int, int]]:
    """
    Extrae los N colores dominantes de una imagen.
    Retorna lista de tuplas (R, G, B).
    """
    with Image.open(ruta) as img:
        img = img.convert('RGB')

        # Reducir para acelerar el análisis
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)

        # Quantizar a N colores y extraer la paleta
        img_p = img.quantize(colors=n_colores, method=Image.Quantize.MEDIANCUT)
        paleta_raw = img_p.getpalette()

        if not paleta_raw:
            return []

        # Contar frecuencia de cada color en la imagen quantizada
        pixels = list(img_p.getdata()) # type: ignore
        frecuencias = {}
        for px in pixels:
            frecuencias[px] = frecuencias.get(px, 0) + 1

        # Ordenar índices por frecuencia descendente
        indices_ordenados = sorted(frecuencias, key=lambda i: frecuencias[i], reverse=True)

        colores = []
        for idx in indices_ordenados[:n_colores]:
            r = paleta_raw[idx * 3]
            g = paleta_raw[idx * 3 + 1]
            b = paleta_raw[idx * 3 + 2]
            colores.append((r, g, b))

        return colores


def rgb_a_hex(rgb: tuple[int, int, int]) -> str:
    return '#{:02X}{:02X}{:02X}'.format(*rgb)


def rgb_a_hsl(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    mx, mn = max(r, g, b), min(r, g, b)
    delta = mx - mn
    l = (mx + mn) / 2

    if delta == 0:
        h = s = 0
    else:
        s = delta / (1 - abs(2 * l - 1))
        if mx == r:
            h = ((g - b) / delta) % 6
        elif mx == g:
            h = (b - r) / delta + 2
        else:
            h = (r - g) / delta + 4
        h = round(h * 60)
        if h < 0:
            h += 360

    return (int(h), int(s * 100), int(l * 100))


def es_color_claro(rgb: tuple[int, int, int]) -> bool:
    """Determina si el color es suficientemente claro para usar texto oscuro."""
    r, g, b = rgb
    luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminancia > 0.5


def formatos_color(rgb: tuple[int, int, int]) -> dict[str, str]:
    """Retorna todos los formatos del color."""
    h, s, l = rgb_a_hsl(rgb)
    return {
        'HEX':      rgb_a_hex(rgb),
        'RGB':      f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]})',
        'HSL':      f'hsl({h}, {s}%, {l}%)',
        'CSS var':  f'--color: {rgb_a_hex(rgb)};',
    }

def exportar_paleta_imagen(
    paleta: list[tuple[int, int, int]],
    ruta_salida: str,
    ancho_swatch: int = 120,
    alto_swatch: int = 120,
    padding: int = 20,
    mostrar_hex: bool = True
) -> str:
    """
    Genera una imagen PNG con los swatches de la paleta.
    Retorna la ruta del archivo guardado.
    """
    from PIL import ImageDraw, ImageFont

    n = len(paleta)
    ancho_total = ancho_swatch * n + padding * (n + 1)
    alto_texto = 28 if mostrar_hex else 0
    alto_total = alto_swatch + padding * 2 + alto_texto

    img = Image.new('RGB', (ancho_total, alto_total), (18, 18, 20))
    draw = ImageDraw.Draw(img)

    # Intentar cargar fuente — si no hay, usa default
    try:
        fuente = ImageFont.truetype('assets/fonts/Inter.ttf', 14)
    except Exception:
        fuente = ImageFont.load_default()

    for i, rgb in enumerate(paleta):
        x = padding + i * (ancho_swatch + padding)
        y = padding

        # Swatch redondeado
        draw.rounded_rectangle(
            [x, y, x + ancho_swatch, y + alto_swatch],
            radius=12,
            fill=rgb
        )

        # HEX debajo
        if mostrar_hex:
            hex_str = rgb_a_hex(rgb)
            text_color = (30, 30, 30) if es_color_claro(rgb) else (200, 200, 200)

            # Centrar texto
            bbox = draw.textbbox((0, 0), hex_str, font=fuente)
            text_w = bbox[2] - bbox[0]
            text_x = x + (ancho_swatch - text_w) // 2
            text_y = y + alto_swatch + 8

            draw.text((text_x, text_y), hex_str, fill=(180, 180, 190), font=fuente)

    img.save(ruta_salida, 'PNG', optimize=True)
    return ruta_salida


def extraer_paleta_safe(ruta: str, n_colores: int = 6) -> tuple[list[tuple[int, int, int]], str | None]:
    """Wrapper seguro que devuelve (paleta, error)."""
    try:
        return extraer_paleta(ruta, n_colores), None
    except Exception as exc:
        return [], str(exc)
