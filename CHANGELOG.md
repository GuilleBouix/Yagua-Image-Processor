# Changelog

Todos los cambios notables del proyecto se documentan en este archivo.

## [2.0.0] - En preparación

### Yagua 2.0

- Versión técnica 2.0.0 para Windows x86-64 (instalador y portable) y Linux x86-64 (AppImage).
- Interfaz unificada, precarga de los módulos visibles sin inicializar los motores de IA y reutilización de previews y miniaturas.
- Consulta, edición, limpieza y exportación de metadatos por lotes, con previews y borradores independientes.
- Guardado mediante copias o sobrescritura con publicación atómica y protección frente a conflictos de nombres.
- Compresión que descarta resultados iguales o mayores que el original; el módulo Comprimir ya no ofrece eliminar EXIF.
- Nueve idiomas de interfaz y acceso a la web oficial y su documentación.

### Actualizaciones y migración desde las RC

- El actualizador de 2.0.0 consulta el repositorio oficial Yagua-Image-Processor y ofrece únicamente versiones estables superiores de la misma plataforma. Descarta borradores y versiones preliminares, aunque el tag y la marca de GitHub no coincidan.
- Quienes tengan 2.0.1-rc deben descargar e instalar 2.0.0 manualmente una vez: para la comparación de versiones, 2.0.0 es inferior a 2.0.1-rc. Ocultar las releases RC no modifica el actualizador de las aplicaciones ya instaladas.
- La actualización sigue abriendo la página de descarga; no instala paquetes automáticamente.
- Las releases RC continuarán públicas durante la preparación. Sólo se pasarán a borradores al aprobar el lanzamiento; se conservarán sus tags y archivos.

### Estado de preparación

- Esta entrada prepara las notas de Yagua 2.0; todavía no anuncia una release publicada.
- Pendientes la estabilización y validación completa del código, los paquetes finales, la aceptación en escritorios limpios y el cierre de los requisitos de distribución.

## [2.0.1-rc.7] - 2026-10-16

### Prueba de actualización en Windows

- Prerelease solo para Windows, con instalador y portable, para comprobar que la RC.6 detecta una versión posterior desde Ajustes.
- Conserva las funciones, modelos, calidad y nueve idiomas de la RC.6; incluye los README en nueve idiomas y la captura de inicio incorporados a main.
- La actualización abre la página de descarga; la instalación sigue siendo manual.
- No se genera una RC.7 de Linux. Las publicaciones anteriores se conservan.

## [2.0.1-rc.6] - 2026-10-16

### Idiomas e interfaz

- Italiano, japonés, chino simplificado y ruso: nueve idiomas de interfaz, con selección y persistencia mediante Ajustes → Aplicar.
- Fuentes Noto Sans CJK JP/SC Regular y Bold incluidas para uso offline, con licencia y revisión fija; registro privado en Windows y Linux.
- Nombres nativos legibles en el selector de idiomas y contratos de las opciones conservados. OCR sigue reconociendo únicamente español, inglés y ambos.

### Actualizaciones

- El comprobador detecta la versión superior de cada plataforma entre releases estables y prereleases; ignora borradores y versiones de otro sistema operativo.
- Un fallo de conexión o de respuesta de GitHub se distingue de «No hay actualizaciones». La comprobación al iniciar sigue sin bloquear la app.
- La actualización abre una descarga: la instalación sigue siendo manual.
- Los paquetes RC.4/RC.5 ya publicados conservan el comprobador anterior: para pasar a esta RC hace falta descargarla e instalarla manualmente una vez.

### Paquetes y comprobaciones

- Comprobación de fuentes incluidas y familias disponibles en Tk en los paquetes finales, y conservación de Xft/Fontconfig en Linux.
- Regresiones de idiomas, parámetros, preferencias, selectores, OCR y errores del actualizador.
- Las fuentes añaden 66.94 MB sin comprimir. Se mantiene el límite instalado de 2 GB incluyendo modelos y cachés; cada paquete debe superar las verificaciones antes de publicarse.
- Informes de auditoría fuera del seguimiento de Git, conservados localmente.

### Límites de esta prerelease

- Versión de prueba para instalador y portable Windows x86-64 y AppImage Linux x86-64.
- Pendientes la revisión lingüística por hablantes nativos y la aceptación visual y de instalación en equipos limpios.
- Los modelos OCR y quitar fondo siguen descargándose en el primer uso y reutilizándose offline.

## [2.0.1-rc.5] - 2026-10-15

### Seguridad y estabilidad

- Consolidación de la auditoría: guardado mediante temporales, protección contra sobrescrituras, validaciones y preferencias locales resistentes a errores.
- Coordinación global de lotes, descarte de callbacks antiguos y cierre/reinicio que espera las operaciones activas.
- Edición EXIF JPEG sin recomprimir ni perder ICC; rechazo seguro de archivos multipágina no soportados y eliminación efectiva de EXIF al comprimir.
- Corrección de la primera descarga de OCR en consolas Windows CP1252 y conservación de perfiles ICC RGB al convertir a JPEG/WebP.

### Metadatos e interfaz

- Integración de los ajustes del editor de Metadatos: vista previa de la imagen seleccionada, orientación visual y adaptación al tamaño del panel.
- Conservación de las mejoras de rendimiento, diseño y módulos actuales.

### Dependencias y publicación

- Separación de dependencias de ejecución, desarrollo y construcción; OpenCV headless en Windows y Linux.
- Exclusión de herramientas, recursos y dependencias sin uso comprobado, manteniendo modelos, motores, formatos y calidad.
- Modelos OCR y quitar fondo descargados cuando se necesitan y reutilizados localmente sin internet.
- Checks de lint, tipado, tests con Tk obligatorio y paquetes reales; verificaciones online/offline, integridad de modelos y máximo instalado de 2 GB incluyendo modelos y cachés.

### Documentación

- Requisitos de PC actualizados en los README en inglés, español, portugués, francés y alemán: mínimo práctico provisional de 8 GB de RAM y CPU de cuatro núcleos; recomendados 16 GB, CPU moderna de seis a ocho núcleos y SSD.
- Diferenciación entre estimaciones de hardware, mediciones observadas y compatibilidad comprobada.

### Límites de esta prerelease

- Versión de prueba para Windows x86-64 (instalador y portable) y Linux x86-64 (AppImage).
- La validación de paquetes se realiza automáticamente antes de publicar. Siguen pendientes la aceptación en equipos de gama baja, instalación/desinstalación en equipos limpios y la matriz visual de escritorios Linux.
- No se garantiza un máximo de RAM ni un tiempo de procesamiento para todas las fotografías. Los modelos deben estar descargados para usar cada opción sin conexión.

## [2.0.0 (preparación histórica)] - 2026-04-09

Registro de la preparación de abril, conservado como antecedente. No describe la
release estable actual e incluye funciones que después se retiraron.

### Nuevas features

- Pantalla de bienvenida (Home) al iniciar.
- OCR con EasyOCR (carga en background).
- Marca de agua con preview en tiempo real y soporte de PNG transparente.
- Vectorización a SVG (vtracer) con validación de formatos y límites de seguridad.
- Transformaciones de imagen (rotación/flip/EXIF).
- Soporte HEIC/HEIF global (Pillow + pillow-heif).

### UX / UI

- Ajustes con tabs (Ajustes / Actualizaciones).
- Actualizaciones simplificadas: solo “check + link” a la última Release (sin instalación automática).
- UI más consistente y compacta en módulos nuevos.

### Fixes

- Lectura robusta de rutas Unicode/acentos en OpenCV (imdecode/fromfile).
- Metadata: edición de fechas EXIF (DateTime / DateTimeOriginal / DateTimeDigitized) + validación de formato.

### Build / CI

- CI: Windows (suite completa) + Linux/macOS (core).
- Release Windows: PyInstaller + Inno Setup + portable zip + hashes + `latest.json`.
- Base macOS: script de build con PyInstaller (`scripts/build_macos_app.sh`).

### Notas

- `v1.1.2` fue la última versión estable previa a `v2.0.0`.

## [1.2.3] - 2026-04-08

### Fixes

- Re-release para asegurar distribución correcta de la v1.2.2 (idioma Alemán) y pruebas de auto-update.

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
