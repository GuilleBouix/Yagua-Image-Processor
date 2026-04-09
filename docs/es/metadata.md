# Metadatos (EXIF)

## Overview
Permite ver/editar metadatos EXIF (incluyendo fechas) y limpiar EXIF en lote.

## Inputs soportados
- Editar EXIF: `JPG/JPEG` y `TIFF` (formatos con EXIF)
- Limpieza en lote (UI): hasta 100 imágenes

## Outputs
- Archivo sobrescrito o guardado con cambios (según flujo del módulo).
- Para limpieza en lote: archivos limpios en carpeta destino.

## Workflow
### Editar
1. Seleccionar imagen con EXIF.
2. Editar campos (Autor, Software, Fechas, etc.).
3. Guardar cambios.

### Limpiar en lote
1. Seleccionar imágenes.
2. Elegir carpeta de salida.
3. Ejecutar limpieza.

## Errores comunes
- Formato de fecha inválido: usar `YYYY:MM:DD HH:MM:SS`.
- Imágenes sin EXIF: se guarda sin EXIF (aviso).

## Troubleshooting
- Si “guardé pero no cambió”: reabrir el archivo desde el módulo para confirmar que se escribió.

## Ejemplos
- Cambiar `DateTimeOriginal` a `2026:04:09 12:00:00`.

## Notas técnicas
- Fechas típicas:
  - `DateTime`: fecha/hora del archivo (IFD 0)
  - `DateTimeOriginal`: momento de captura (ExifIFD)
  - `DateTimeDigitized`: momento de digitalización (ExifIFD)

## Limitaciones
- No todos los formatos soportan EXIF editable.

## Performance tips
- Para lotes grandes, usar carpetas de salida en SSD.

