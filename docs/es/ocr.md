# OCR (Extraer texto)

## Overview
Extrae texto desde imágenes usando EasyOCR (en local).

## Inputs soportados
- Formatos típicos: `JPG`, `PNG`, `WEBP`, `TIFF`, `BMP`, `HEIC`, `HEIF`
- `AVIF`: solo si el runtime de Pillow tiene soporte AVIF; si no, se omite con aviso.
- Lote máximo: 10 imágenes

## Outputs
- Texto extraído (vista previa y exportación desde la UI)

## Workflow
1. Entrar al módulo OCR (carga del motor en background).
2. Seleccionar imágenes.
3. Elegir idioma(s).
4. Procesar OCR.
5. Copiar o exportar el texto.

## Errores comunes
- Congelamiento al abrir: si ocurre, revisa CPU/RAM y `yagua.log` (EasyOCR inicializa modelos).
- “No se pudo abrir la imagen”: archivo corrupto o formato sin soporte en Pillow.

## Troubleshooting
- Si AVIF no funciona: instalar soporte AVIF en Pillow (según plataforma).
- Si OCR es lento: es normal en CPU; GPU acelera significativamente.

## Ejemplos
- Extraer texto de 5 `PNG` en español/inglés y exportar a `.txt`.

## Notas técnicas
- El `Reader` se cachea por combinación de idiomas para evitar reinicializaciones costosas.

## Limitaciones
- OCR depende del contenido: textos muy pequeños o borrosos reducen precisión.

## Performance tips
- Usar imágenes nítidas y recortadas al área de texto.
- Reducir el lote si tu PC tiene poca RAM.

