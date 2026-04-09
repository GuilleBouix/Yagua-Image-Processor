# LQIP / Base64

## Overview
Genera LQIP (Low Quality Image Placeholder) y/o Base64 para uso web.

## Inputs soportados
- Imágenes raster típicas: `JPG`, `PNG`, `WEBP`, `AVIF`, `HEIC`, `HEIF`, etc.
- Lote máximo (UI): 100 imágenes

## Outputs
- Strings/Base64 para copiar/exportar.
- (Según módulo) archivos auxiliares o salida embebida.

## Workflow
1. Seleccionar imágenes.
2. Elegir tamaño/calidad de placeholder.
3. Generar.
4. Copiar/exportar.

## Errores comunes
- Si una imagen falla: suele estar corrupta o tener un formato no soportado.

## Troubleshooting
- Revisar `yagua.log` para el archivo específico que falló.

## Ejemplos
- Generar LQIP para 20 imágenes web.

## Notas técnicas
- Se escapa HTML y se sanitiza CSS para evitar inyección en outputs.

## Limitaciones
- LQIP es un placeholder: no reemplaza la imagen real.

## Performance tips
- Bajar resolución del placeholder para mayor velocidad.

