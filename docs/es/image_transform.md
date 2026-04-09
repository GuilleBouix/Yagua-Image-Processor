# Transformar imágenes

## Overview
Aplica transformaciones simples en lote: rotación, flip y corrección EXIF.

## Inputs soportados
- Formatos típicos: `JPG`, `PNG`, `WEBP`, `TIFF`, `HEIC`, `HEIF`, etc.
- Lote máximo: 100 imágenes

## Outputs
- Imágenes transformadas (mismo formato o formato elegido por el módulo, según opción).

## Workflow
1. Seleccionar imágenes.
2. Configurar rotación/flip/opciones EXIF.
3. Elegir carpeta de salida.
4. Procesar.

## Errores comunes
- “No se pudo abrir la imagen”: archivo corrupto o formato no soportado.

## Troubleshooting
- En JPG sin alpha, el guardado se fuerza a `RGB` para evitar errores.
- Si ves rotaciones inesperadas: desactivar/activar corrección EXIF según el caso.

## Ejemplos
- Rotar 90° y hacer flip horizontal a 50 imágenes.

## Notas técnicas
- Se usa `with Image.open(...)` para asegurar cierre de archivos.

## Limitaciones
- No es un editor avanzado; apunta a transformaciones rápidas por lote.

## Performance tips
- Evitar rutas de red para outputs.
- Para lotes grandes, procesar por tandas.

