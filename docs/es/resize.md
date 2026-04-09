# Redimensionar

## Overview
Redimensiona imágenes en lote manteniendo proporción (según opciones).

## Inputs soportados
- Formatos típicos: `JPG`, `PNG`, `WEBP`, `TIFF`, `HEIC`, `HEIF`, etc.
- Lote máximo (UI): 100 imágenes

## Outputs
- Imágenes redimensionadas en la carpeta de salida.

## Workflow
1. Seleccionar imágenes.
2. Configurar tamaño (ancho/alto) y opciones.
3. Elegir carpeta de salida.
4. Procesar.

## Errores comunes
- Si el archivo no abre: puede estar corrupto o no soportado.

## Troubleshooting
- Para mantener transparencia, usar formatos que soporten alpha (`PNG/WEBP/TIFF/HEIF`).

## Ejemplos
- Redimensionar a 1200px de ancho manteniendo aspect ratio.

## Notas técnicas
- Se conserva alpha si el formato de salida lo soporta.

## Limitaciones
- La calidad final depende del método de resample.

## Performance tips
- Evitar lotes máximos en PCs con poca RAM.

