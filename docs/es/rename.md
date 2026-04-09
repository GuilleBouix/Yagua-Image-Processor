# Renombrar

## Overview
Renombra archivos en lote con vista previa y sanitización de nombres.

## Inputs soportados
- Archivos de imagen (según selector del módulo)
- Lote máximo (UI): 100 archivos

## Outputs
- Archivos renombrados (en la misma carpeta o según el flujo del módulo).

## Workflow
1. Seleccionar archivos.
2. Configurar prefijo/sufijo/contador.
3. Previsualizar.
4. Aplicar.

## Errores comunes
- Conflictos de nombres: el módulo omite/evita sobreescrituras.

## Troubleshooting
- Evitar caracteres inválidos para Windows (`<>:\"/\\|?*`).

## Ejemplos
- `producto_001.jpg`, `producto_002.jpg`, …

## Notas técnicas
- Se sanitizan prefijos para evitar rutas inválidas o inyección de caracteres.

## Limitaciones
- Renombrar no modifica el contenido del archivo, solo el nombre.

## Performance tips
- Para lotes grandes, usar carpetas locales.

