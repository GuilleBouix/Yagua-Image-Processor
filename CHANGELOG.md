# Changelog

Todos los cambios notables del proyecto se documentan en este archivo.

## [1.0.0] - 2026-03-25

- Primera versión estable.
- Módulos de procesamiento: comprimir, convertir, redimensionar, metadatos, quitar fondo, renombrar, lqip.
- Manejo de conflictos en los archivos de salida para evitar sobreescrituras.
- Tareas en segundo plano para evitar congelamientos de la UI en operaciones pesadas.
- Traducciones y etiquetas de UI mejoradas y consistentes.
- Configuración guardada en AppData para persistencia estable de tema e idioma.
- Build con PyInstaller en modo one-folder con assets e imports dinámicos incluidos.

## [1.1.0] - 2026-03-26

- Límites de lote por módulo para mejorar el rendimiento (100 imágenes, quitar fondo 10).
- Suites de tests de core y UI con pytest.
- Limpieza PEP8 y mejoras de legibilidad en nombres.
- README simplificado con instrucciones de instalación y uso más claras.

## [1.1.1] - 2026-03-27

- Sidebar configurable con selecci?n de m?dulos visibles desde Ajustes.
- Bot?n "Aplicar" para evitar reinicios al cambiar opciones.
- Sidebar con scroll solo si hay m?s de un m?dulo visible.
- Loader interno en "Quitar fondo" (no bloquea la pantalla).
- Botones de apoyo/donaci?n en sidebar y Ajustes (PayPal).
- Logs mejorados para errores en "Quitar fondo".
