# Comprimir

## Overview
Reduce el tamaño de imágenes con control de calidad.

## Inputs soportados
- Formatos típicos: `JPG`, `PNG`, `WEBP`, `AVIF`, `HEIC`, `HEIF`, `TIFF`
- Lote máximo (UI): 100 imágenes

## Outputs
- Imágenes comprimidas (formato según UI/módulo).

## Workflow
1. Seleccionar imágenes.
2. Ajustar calidad.
3. Elegir carpeta de salida.
4. Comprimir.

## Errores comunes
- Calidad extrema: puede degradar mucho el resultado (artefactos visibles).

## Troubleshooting
- Si una imagen falla, revisar `yagua.log` para identificar el archivo.

## Ejemplos
- Comprimir 100 `JPG` al 80% de calidad.

## Notas técnicas
- Para formatos con `quality` (AVIF/HEIF/WEBP/JPEG) se aplica el parámetro de calidad.

## Limitaciones
- Algunos formatos dependen del soporte del runtime (AVIF/HEIF).

## Performance tips
- Para lotes grandes, exportar a disco local.

