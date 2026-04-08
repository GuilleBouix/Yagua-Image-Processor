# Changelog

Todos los cambios notables del proyecto se documentan en este archivo.

## [Unreleased]

_Sin cambios documentados todavía._

## [1.2.2] - 2026-04-08

### UX / UI
- Nuevo idioma: Alemán.

## [1.2.1] - 2026-04-08

### UX / UI
- Nuevo idioma: Francés.

## [1.2.0] - 2026-04-08

### Nuevas features
- OCR con EasyOCR.
- Marca de agua con preview en tiempo real.
- Vectorización a SVG.
- Transformaciones de imagen (rotación, flip, EXIF).
- Soporte HEIC/HEIF en lectura y conversión.
- Auto-updater (Windows/Inno): buscar, descargar, verificar e instalar actualizaciones desde Ajustes.

### UX / UI
- Ajustes con tabs (Ajustes / Actualizaciones).
- Mejoras de mensajes y validaciones en Metadata (fechas EXIF).
- UI más compacta y consistente en módulos nuevos.
- Dropdowns/presets traducidos y consistentes (Vectorizar, Watermark, OCR).

### Fixes
- Lectura robusta de rutas con caracteres especiales en varios modulos.
- Correcciones en edicion de metadatos EXIF.

### Build / Packaging
- PyInstaller actualizado con imports dinamicos y assets nuevos.
- Dependencias actualizadas para OCR y HEIC.
- CI/CD Windows: build + instalador + releases automáticos con hashes.

## [1.1.1] - 2026-03-27

- Sidebar configurable con seleccion de modulos visibles desde Ajustes.
- Boton "Aplicar" para evitar reinicios al cambiar opciones.
- Sidebar con scroll solo si hay mas de un modulo visible.
- Loader interno en "Quitar fondo" (no bloquea la pantalla).
- Botones de apoyo/donacion en sidebar y Ajustes (PayPal).
- Logs mejorados para errores en "Quitar fondo".

## [1.1.0] - 2026-03-26

- Limites de lote por modulo para mejorar el rendimiento (100 imagenes, quitar fondo 10).
- Suites de tests de core y UI con pytest.
- Limpieza PEP8 y mejoras de legibilidad en nombres.
- README simplificado con instrucciones de instalacion y uso mas claras.

## [1.0.0] - 2026-03-25

- Primera version estable.
- Modulos de procesamiento: comprimir, convertir, redimensionar, metadatos, quitar fondo, renombrar, lqip.
- Manejo de conflictos en los archivos de salida para evitar sobreescrituras.
- Tareas en segundo plano para evitar congelamientos de la UI en operaciones pesadas.
- Traducciones y etiquetas de UI mejoradas y consistentes.
- Configuracion guardada en AppData para persistencia estable de tema e idioma.
- Build con PyInstaller en modo one-folder con assets e imports dinamicos incluidos.
