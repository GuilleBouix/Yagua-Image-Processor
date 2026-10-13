# LQIP / Base64

## Overview
Genera LQIP (Low Quality Image Placeholder) y/o Base64 para uso web.

## Inputs soportados
- Imágenes raster típicas: `JPG`, `PNG`, `WEBP`, `AVIF`, `HEIC`, `HEIF`, etc.
- Una imagen por vez en LQIP y Base64.

## Outputs
- Strings/Base64 para copiar/exportar.
- (Según módulo) archivos auxiliares o salida embebida.

## Workflow
1. Seleccionar una imagen.
2. Elegir LQIP o Base64 y ajustar sus parámetros.
3. Generar y comparar el original con el resultado.
4. Elegir Data URI, HTML, CSS o Base64 puro y copiar/exportar.

Al cargar otra imagen se descarta el resultado y se restablecen el modo LQIP,
el ancho de 20 px, desenfoque 2, calidad LQIP 40 y calidad Base64 85.
Cancelar el selector conserva la imagen y los ajustes actuales.

## Errores comunes
- Si una imagen falla: suele estar corrupta o tener un formato no soportado.

## Troubleshooting
- Revisar `yagua.log` para el archivo específico que falló.

## Ejemplos
- Generar un placeholder de 20 px para una imagen web.

## Notas técnicas
- Se escapa HTML y se sanitiza CSS para evitar inyección en outputs.

## Limitaciones
- LQIP es un placeholder: no reemplaza la imagen real.

## Performance tips
- Bajar resolución del placeholder para mayor velocidad.

