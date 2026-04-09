# Convertir

## Overview
Convierte imágenes entre formatos (incluye HEIC como salida si el soporte está instalado).

## Inputs soportados
- Formatos típicos: `JPG`, `PNG`, `WEBP`, `BMP`, `TIFF`, `GIF`, `AVIF`, `HEIC`, `HEIF`
- Lote máximo (UI): 100 imágenes

## Outputs
- Formatos de salida (según UI): `JPEG`, `PNG`, `WEBP`, `AVIF`, `HEIC`, `ICO`, `BMP`, `TIFF`, `GIF`

## Workflow
1. Seleccionar imágenes.
2. Elegir formato destino y calidad (si aplica).
3. Elegir carpeta de salida.
4. Convertir.

## Errores comunes
- HEIC no disponible: falta `pillow-heif` o no se registró el opener.
- AVIF no disponible: depende del soporte AVIF en Pillow en tu plataforma.

## Troubleshooting
- Revisar `yagua.log` si una imagen en particular falla y el resto no.
- Probar convertir primero a `PNG` si el archivo de entrada es problemático.

## Ejemplos
- Convertir `WEBP` → `JPEG` con calidad 90.

## Notas técnicas
- Para `HEIC`, internamente se guarda como `HEIF` con extensión `.heic`.

## Limitaciones
- Algunos formatos pueden no estar soportados en todos los sistemas (depende de wheels/codec).

## Performance tips
- Evitar carpetas de salida en la nube/unidades lentas.

