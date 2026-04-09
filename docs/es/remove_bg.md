# Quitar fondo (Remove BG)

## Overview
Elimina el fondo de imágenes usando `rembg` (U^2-Net). Tras la primera descarga del modelo, funciona offline.

## Inputs soportados
- Formatos típicos: `JPG`, `PNG`, `WEBP`, `TIFF`, `BMP`, `HEIC`, `HEIF`
- Lote máximo: 10 imágenes

## Outputs
- Imágenes con fondo removido (según formato elegido en la UI, comúnmente `PNG`/`WEBP`).

## Workflow
1. Abrir el módulo (puede descargar el modelo la primera vez).
2. Seleccionar imágenes.
3. Elegir formato de salida y carpeta.
4. Procesar.

## Errores comunes
- Descarga del modelo falla: conexión bloqueada/firewall o sin internet.
- “No se pudo abrir la imagen”: archivo corrupto o formato no soportado.

## Troubleshooting
- Si falla la descarga: probar otra red o permitir acceso a GitHub/hosting del modelo.
- Si la salida no tiene transparencia: usar salida `PNG`/`WEBP` con alpha.

## Ejemplos
- Quitar fondo a 10 imágenes `JPG` y exportar a `PNG`.

## Notas técnicas
- La sesión de `rembg` se crea por modelo y se reutiliza para batch.

## Limitaciones
- La calidad depende del contraste sujeto/fondo.
- Primer uso puede tardar por la descarga del modelo.

## Performance tips
- Procesar por lotes chicos si la PC tiene poca RAM.
- Evitar rutas de red para outputs.

