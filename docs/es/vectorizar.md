# Vectorizar (SVG)

## Overview
Convierte imágenes raster a SVG usando `vtracer`.

## Inputs soportados
- Formatos: `PNG`, `WEBP`, `TIFF`, `HEIC`, `HEIF`
- Lote máximo: 50 imágenes
- Límite de tamaño: se omiten archivos de más de 1 MB

## Outputs
- `SVG` (1 archivo `.svg` por imagen)

## Workflow
1. Seleccionar imágenes.
2. Ajustar preset/parámetros.
3. Elegir carpeta de salida.
4. Exportar.

## Errores comunes
- “Formato no soportado”: seleccionaste un formato fuera de la lista (por ejemplo `JPG`).
- “Archivo demasiado grande”: la imagen supera 1 MB.
- “vtracer no está instalado”: falta la dependencia en el entorno.

## Troubleshooting
- Si no aparece el SVG: revisa `yagua.log` y valida permisos de escritura en la carpeta destino.
- Si falla con HEIC/HEIF: confirma que `pillow-heif` esté instalado y que el soporte HEIF se registre al iniciar la app.

## Ejemplos
- Exportar un lote de `PNG` con preset “Foto” a una carpeta `output/`.

## Notas técnicas
- En Windows se normalizan rutas para evitar backslashes en `vtracer`.

## Limitaciones
- No acepta `JPG` por diseño (para priorizar flujos con transparencia).
- El resultado puede diferir visualmente del raster original (vectorización).

## Performance tips
- Mantén archivos pequeños (ideal: < 1 MB) para mejorar velocidad y evitar omisiones.
- Para lotes grandes, exporta en carpetas locales (no unidades de red).

