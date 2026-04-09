# Marca de agua (Watermark)

## Overview
Aplica una marca de agua a un lote de imágenes. La vista previa es en tiempo real usando la primera imagen del lote.

## Inputs soportados
- Imágenes base: formatos típicos (`JPG`, `PNG`, `WEBP`, `TIFF`, `HEIC`, `HEIF`, etc.)
- Marca de agua: `PNG` (recomendado, soporta transparencia), `WEBP`, etc.
- Lote máximo: 100 imágenes

## Outputs
- Imágenes exportadas con la marca aplicada (según formato destino del módulo).

## Workflow
1. Seleccionar imágenes base (hasta 100).
2. Seleccionar 1 imagen de marca de agua.
3. Ajustar preset/posición/tamaño/opacidad/margen.
4. Aplicar y elegir carpeta de salida.

## Errores comunes
- Fondo “extraño” en watermark: suele pasar si la marca no tiene alpha real (exportar como PNG con transparencia).
- Preview en negro: revisar que la imagen base y la marca se carguen correctamente; revisar `yagua.log`.

## Troubleshooting
- Preferir watermark `PNG` con transparencia real.
- Si hay rutas con acentos/símbolos: la carga está preparada para Unicode en Windows, pero revisa permisos/paths.

## Ejemplos
- Aplicar un logo semitransparente en “abajo derecha” con margen 20px.

## Notas técnicas
- La preview se calcula con una versión reducida para mantener fluidez.

## Limitaciones
- La preview no representa pixel-perfect el resultado final si la imagen es muy grande (solo es una aproximación).

## Performance tips
- Mantener la marca de agua en tamaño razonable.
- Para lotes grandes, evitar discos externos lentos.

