"""
Modulo de extraccion de paleta de colores.
Extrae colores dominantes de imagenes y genera paletas visuales.

Relacionado con:
    - app/core/__init__.py: Re-exporta las funciones de este modulo.
    - app/ui/frames/palette/services.py: Usa las funciones de este modulo.
"""

from pathlib import Path

from PIL import Image


def cargar_preview(ruta, size=(80, 80)):
    """
    Carga una imagen y genera una vista previa en miniatura.
    
    Args:
        ruta: Ruta de la imagen.
        size: Tamano maximo de la vista previa (ancho, alto).
        
    Returns:
        Tupla con (imagen_preview, ancho_original, alto_original, extension).
    """
    with Image.open(ruta) as imagen:
        ancho, alto = imagen.size
        imagen = imagen.convert('RGB')
        imagen.thumbnail(size, Image.Resampling.LANCZOS)
        preview = imagen.copy()
    extension = Path(ruta).suffix.upper().lstrip(".")
    return preview, ancho, alto, extension


def extraer_paleta(ruta, n_colores=6):
    """
    Extrae los N colores dominantes de una imagen.
    
    Usa cuantizacion con el algoritmo MEDIANCUT para identificar
    los colores mas representativos de la imagen.
    
    Args:
        ruta: Ruta de la imagen.
        n_colores: Cantidad de colores a extraer (default 6).
        
    Returns:
        Lista de tuplas (red, green, blue) con los colores dominantes.
    """
    with Image.open(ruta) as imagen:
        imagen = imagen.convert('RGB')

        # Reducir tamano para acelerar el analisis
        imagen.thumbnail((400, 400), Image.Resampling.LANCZOS)

        # Cuantizar a N colores usando MEDIANCUT
        img_quantized = imagen.quantize(colors=n_colores, method=Image.Quantize.MEDIANCUT)
        paleta_raw = img_quantized.getpalette()

        if not paleta_raw:
            return []

        # Contar frecuencia de cada color en la imagen cuantizada
        pixels = list(img_quantized.getdata())
        frecuencias = {}
        for px in pixels:
            frecuencias[px] = frecuencias.get(px, 0) + 1

        # Ordenar indices por frecuencia descendente
        indices_ordenados = sorted(frecuencias, key=lambda i: frecuencias[i], reverse=True)

        # Extraer colores RGB de los indices mas frecuentes
        colores = []
        for indice in indices_ordenados[:n_colores]:
            red = paleta_raw[indice * 3]
            green = paleta_raw[indice * 3 + 1]
            blue = paleta_raw[indice * 3 + 2]
            colores.append((red, green, blue))

        return colores


def rgb_a_hex(rgb_tuple):
    """
    Convierte color RGB a formato hexadecimal.
    
    Args:
        rgb_tuple: Tupla (red, green, blue) con valores 0-255.
        
    Returns:
        Cadena hexadecimal (ej: '#FF5733').
    """
    return '#{:02X}{:02X}{:02X}'.format(*rgb_tuple)


def rgb_a_hsl(rgb_tuple):
    """
    Convierte color RGB a HSL (Hue, Saturation, Lightness).
    
    Args:
        rgb_tuple: Tupla (red, green, blue) con valores 0-255.
        
    Returns:
        Tupla (H, S, L) con H en grados (0-360), S y L en porcentaje (0-100).
    """
    red, green, blue = rgb_tuple[0] / 255, rgb_tuple[1] / 255, rgb_tuple[2] / 255
    max_val, min_val = max(red, green, blue), min(red, green, blue)
    diferencia = max_val - min_val
    l = (max_val + min_val) / 2

    # Calcular matiz y saturacion
    if diferencia == 0:
        h = s = 0
    else:
        s = diferencia / (1 - abs(2 * l - 1))
        if max_val == red:
            h = ((green - blue) / diferencia) % 6
        elif max_val == green:
            h = (blue - red) / diferencia + 2
        else:
            h = (red - green) / diferencia + 4
        h = round(h * 60)
        if h < 0:
            h += 360

    return (int(h), int(s * 100), int(l * 100))


def es_color_claro(rgb_tuple):
    """
    Determina si el color es suficientemente claro.
    
    Usa la formula de luminancia ponderada para determinar
    si el color requiere texto oscuro o claro para ser legible.
    
    Args:
        rgb_tuple: Tupla (red, green, blue) con valores 0-255.
        
    Returns:
        True si el color es claro (mas de 50% de luminancia).
    """
    red, green, blue = rgb_tuple
    # Formula de luminancia estandar
    luminancia = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
    return luminancia > 0.5


def formatos_color(rgb_tuple):
    """
    Genera todos los formatos de representacion de un color.
    
    Args:
        rgb_tuple: Tupla (red, green, blue) con valores 0-255.
        
    Returns:
        Diccionario con los formatos: HEX, RGB, HSL y CSS var.
    """
    h, s, l = rgb_a_hsl(rgb_tuple)
    return {
        'HEX':      rgb_a_hex(rgb_tuple),
        'RGB':      f'rgb({rgb_tuple[0]}, {rgb_tuple[1]}, {rgb_tuple[2]})',
        'HSL':      f'hsl({h}, {s}%, {l}%)',
        'CSS var':  f'--color: {rgb_a_hex(rgb_tuple)};',
    }


def exportar_paleta_imagen(paleta, ruta_salida, ancho_swatch=120,
                          alto_swatch=120, padding=20, mostrar_hex=True):
    """
    Genera una imagen PNG con los swatches de la paleta.
    
    Crea una imagen con cuadrados de color y su codigo HEX
    debajo de cada uno.
    
    Args:
        paleta: Lista de tuplas (red, green, blue).
        ruta_salida: Ruta donde guardar la imagen PNG.
        ancho_swatch: Ancho de cada muestra de color.
        alto_swatch: Alto de cada muestra de color.
        padding: Espacio entre elementos.
        mostrar_hex: Si es True, muestra el codigo HEX debajo de cada color.
        
    Returns:
        Ruta del archivo guardado.
    """
    from PIL import ImageDraw, ImageFont

    n = len(paleta)
    ancho_total = ancho_swatch * n + padding * (n + 1)
    alto_texto = 28 if mostrar_hex else 0
    alto_total = alto_swatch + padding * 2 + alto_texto

    # Crear imagen con fondo oscuro
    imagen = Image.new('RGB', (ancho_total, alto_total), (18, 18, 20))
    draw = ImageDraw.Draw(imagen)

    # Cargar fuente Inter o usar default si no existe
    try:
        fuente = ImageFont.truetype('assets/fonts/Inter.ttf', 14)
    except Exception:
        fuente = ImageFont.load_default()

    # Dibujar cada swatch de color
    for i, rgb_tuple in enumerate(paleta):
        coord_x = padding + i * (ancho_swatch + padding)
        coord_y = padding

        # Dibujar cuadrado redondeado con el color
        draw.rounded_rectangle(
            [coord_x, coord_y, coord_x + ancho_swatch, coord_y + alto_swatch],
            radius=12,
            fill=rgb_tuple
        )

        # Dibujar codigo HEX si esta habilitado
        if mostrar_hex:
            hex_str = rgb_a_hex(rgb_tuple)

            # Centrar texto debajo del swatch
            bbox = draw.textbbox((0, 0), hex_str, font=fuente)
            text_w = bbox[2] - bbox[0]
            text_x = coord_x + (ancho_swatch - text_w) // 2
            text_y = coord_y + alto_swatch + 8

            draw.text((text_x, text_y), hex_str, fill=(180, 180, 190), font=fuente)

    # Guardar imagen
    imagen.save(ruta_salida, 'PNG', optimize=True)
    return ruta_salida


def extraer_paleta_safe(ruta, n_colores=6):
    """
    Wrapper seguro para extraer_paleta que maneja errores.
    
    Args:
        ruta: Ruta de la imagen.
        n_colores: Cantidad de colores a extraer.
        
    Returns:
        Tupla (paleta, mensaje_error). Si hay exito, error es None.
    """
    try:
        return extraer_paleta(ruta, n_colores), None
    except Exception as exc:
        return [], str(exc)
