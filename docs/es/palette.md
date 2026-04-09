# Paleta de colores

## Overview
Extrae una paleta de colores desde una imagen (útil para UI/branding).

## Inputs soportados
- 1 imagen por vez (`JPG/PNG/WEBP/TIFF/AVIF/HEIC/HEIF`, etc.)

## Outputs
- Lista de colores (copiable) y exportación de paleta como imagen.

## Workflow
1. Seleccionar imagen.
2. Elegir cantidad de colores.
3. Extraer.
4. Copiar o guardar.

## Errores comunes
- Si falla la apertura: archivo corrupto o formato no soportado.

## Troubleshooting
- Probar convertir la imagen a `PNG` si falla el input.

## Ejemplos
- Extraer 8 colores de una captura.

## Notas técnicas
- La extracción corre en background y muestra overlay de “Procesando”.

## Limitaciones
- La paleta depende del contenido; imágenes con mucho ruido dan resultados menos útiles.

## Performance tips
- Usar imágenes con buena iluminación/contraste para paletas más limpias.

