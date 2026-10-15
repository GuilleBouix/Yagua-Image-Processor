# Yagua 2.0: registro de aceptación

Resultados detallados en [check-results.json](check-results.json).

Trabajo en `codex/yagua-v2-readiness`, desde main fb58c42. Los ajustes locales previos se conservan. No se publica ningún release.

## Integridad y contratos

- JPEG: editar metadatos sin orientación reemplaza EXIF sin recomprimir. ICC y píxeles decodificados tienen regresión; los campos idénticos no reescriben el original.
- TIFF: las imágenes con varias páginas se rechazan intactas. Las etiquetas de almacenamiento se reconstruyen en una transformación de píxeles.
- Conversión, compresión, resize, limpieza EXIF, quitar fondo, watermark, paleta y exportación OCR usan publicación mediante temporales. Los destinos de lotes se publican sin sobrescribir archivos que aparezcan entretanto.
- Comprimir con quitar EXIF no usa el fallback que copiaba metadatos del original.
- Preferencias JSON: lectura centralizada, estructura y campos conocidos validados; escritura mediante reemplazo. Configuración dañada no impide navegar.
- Lotes: coordinador global; selección y opciones capturadas antes de iniciar. Workers entregan resultados por cola; restauración de controles en errores de inicio/procesamiento y comprobación de existencia antes de actualizar widgets.
- Miniaturas: una sola implementación, identificaciones de filas capturadas; resultados de selecciones anteriores descartados.
- Fallos individuales: contrato con ruta, estado y motivo, además de contadores existentes. Las operaciones gestionadas muestran el detalle sin detener los archivos restantes.
- Cierre espera la operación; reinicio permite esperar o seguir en la aplicación. No hay rollback completo de renombrados ya realizados.

## Matriz por módulo

| Módulo | Protección / escenarios automáticos | Aceptación manual pendiente |
|---|---|---|
| Inicio/navegación | Preferencias inválidas; carga de vistas; callbacks sobre vistas destruidas | Equipo limpio y ventana pequeña |
| Convertir | Formatos, colisiones, Unicode, escritura segura, lote único | Colores en HEIC/AVIF y codecs instalados |
| Comprimir | Calidad capturada, EXIF eliminado, ICC, transparencia LA, fallos parciales | Comparación visual de formatos con pérdida |
| Resize | Dimensiones, crop/canvas, salida segura, opciones capturadas | Orientaciones y transparencia visual |
| Quitar fondo | Dependencias y modelo, fallback, cola y salida segura | Primer modelo con/sin red en paquete final |
| OCR | Error diferido, opciones capturadas, salida TXT segura | Primer modelo e idiomas en paquete final |
| Metadatos | JPEG/TIFF, fechas/GPS/orientación, ICC, no-op, ISO, escritura; limpiar selectores; selecciones Ver/Editar independientes | Etiquetas privadas y perfiles de cámaras de referencia |
| Paleta | Frecuencia de colores y exportación PNG; lote coordinado; entrada corrupta conserva selección/paleta anteriores | Legibilidad de swatches |
| Watermark | Composición, entrada inválida, salida segura y rutas, preview con revisión | Composición y márgenes visuales |
| Renombrar | Nombres inválidos, colisiones, preview con revisión; opciones capturadas | Conflictos reales en FS sensible a mayúsculas |
| LQIP | Validaciones y resultados por revisión; lote único | Exportación/copiar en editores externos |
| Ajustes/actualizador | Validación JSON; errores de red; cola; reinicio diferido | Reiniciar portable/instalado/AppImage |

## Verificación reproducible

```powershell
$env:YAGUA_REQUIRE_UI = '1'
.\.venv\Scripts\python.exe scripts/verify.py -q
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m pyright --pythonpath ./.venv/Scripts/python.exe app
.\.venv\Scripts\python.exe scripts/check_mutations.py
```

`verify.py` utiliza preferencias temporales y bloquea peticiones HTTP. Las regresiones de escritura usan archivos sintéticos. `check_mutations.py` copia el código a temporales y confirma que once protecciones fallan al retirarlas: escritura segura, JPEG, multipágina, ISO, EXIF, lote único, finalizaciones antiguas, widgets destruidos, controles ocupados, destino del editor y colisiones. Resultados en mutation-results.json.

## Escenarios y evidencia

| Escenario | Evidencia automática | Límite |
|---|---|---|
| Un solo lote, incluso con inicios simultáneos | `test_coordinator_allows_only_one_global_operation`, `test_simultaneous_starts_grant_exactly_one_slot` | Una instancia de la app |
| Éxito, fallo del worker y fallo de inicio | `test_each_module_restores_real_controls_after_job`: diez módulos × tres resultados | No simula bloqueo permanente de una biblioteca nativa |
| Finalización fuera de orden y destino destruido | `test_stale_completion_cannot_release_new_operation`, `test_destroyed_owner_receives_no_callbacks`, `test_view_destroy_cancels_owned_timers` | Los timers internos de bibliotecas externas no se sustituyen |
| Secuencias reproducibles de estado | `test_generated_state_sequences`: 100 semillas × 100 acciones | Genera acciones del coordinador; no equivale a todas las secuencias posibles de clics |
| Cerrar/reiniciar durante escritura, o cancelar cierre | `test_close_waits_for_current_write_and_can_be_cancelled`, `test_restart_waits_for_current_write` | Procesos/instaladores reales requieren aceptación del paquete |
| Cancelar diálogos y resultados antiguos de preview | `test_selector_loads_only_one_image_and_cancel_preserves_current`, regresiones LQIP/Watermark | Inspección visual de todos los módulos pendiente |
| Abrir un archivo corrupto en Paleta | `test_corrupt_selection_preserves_previous_state` | Mantiene la selección/paleta anterior y libera los controles |
| Editar A, ver B, guardar A; fallo al cargar editor | `test_view_selection_does_not_redirect_editor_save`, `test_failed_editor_load_preserves_previous_target_and_fields` | Solo JPEG/TIFF de una página editables |
| Disco lleno, permisos y reemplazo fallido | `test_partial_write_preserves_original`, `test_settings_replace_failure_preserves_original`, `test_export_failure_reports_error_and_preserves_existing_file` | Fallos simulados; no prueba cortes eléctricos ni firmware |
| Salida creada por otro proceso durante el guardado | `test_publish_does_not_overwrite_competing_output` | Protección de publicación de outputs; renombrar un lote no tiene rollback completo |
| JPEG: editar autor sin recomprimir ni perder ICC | `test_jpeg_metadata_keeps_pixels_and_profile` | Perfiles/cámaras poco comunes necesitan muestras reales de referencia |
| TIFF multipágina rechazado intacto y privacidad EXIF | `test_multipage_edit_rejected_without_changes`, `test_compression_strips_exif_even_if_larger` | No añade procesamiento de animaciones o páginas múltiples |
| Preferencias dañadas y perfil sin permisos | `test_invalid_preferences`, `test_unwritable_log_directory_does_not_block_startup` | Las preferencias reales no se utilizan en pruebas |
| Idiomas, temas y escalas | `test_modules_construct_across_language_theme_scale`, `test_translation_keys_and_parameters_match`, `test_static_translation_keys_exist`, regresiones de resultados Convertir/Resize | Construcción y contratos; contraste, foco y cortes visuales pendientes |

Los cambios de textos eliminan el sustantivo español incrustado en resultados de Convertir/Resize y traducen los filtros de imágenes de los diálogos, conservando el diseño.

El análisis completo de Pyright quedó reducido de 198 diagnósticos a cero. CI ya no usa skipunannotated; se conserva el nivel basic, que no equivale al modo strict.

## Paquetes y plataformas

| Entorno | Estado |
|---|---|
| Windows 11 Pro 10.0.26200 x64, Python 3.13 | Build PyInstaller y preflight offline del código final aprobados; hash del ejecutable en windows-package-preflight.json |
| Windows CI | Gate de runtime/UI del ejecutable añadido antes del instalador y publicación; pendiente ejecución remota |
| Windows 10/11 x64 limpio, usuario normal sin Python | Pendiente instalador y portable exactos, espacios/acentos, conexión/desconexión |
| Ubuntu 22.04/24.04 y LTS vigente | Pendiente AppImage exacto, FUSE y extracción |
| Debian/Mint/Fedora estables | Pendiente registrar versiones, bibliotecas y primer uso |
| GNOME/KDE/Xfce; X11/Wayland | Pendiente matriz visual y portapapeles |

AppImage requiere bibliotecas compatibles y pruebas en los sistemas destino: [documentación oficial](https://docs.appimage.org/reference/best-practices.html). El formato de distribución no demuestra compatibilidad.

## Checklist de lanzamiento

- [ ] Confirmar que no quedan bloqueadores y volver a ejecutar checks en el commit que se publicará.
- [ ] Completar inspección visual de idiomas, temas, escalas, teclado y ventana pequeña; los tests de construcción no comprueban contraste ni controles cortados.
- [ ] Aprobar CI Windows/Linux en el commit final.
- [ ] Construir los artefactos finales, anotar commit y SHA256, ejecutar las pruebas sobre esos mismos archivos.
- [ ] Primer OCR/quitar fondo con red, luego repetir sin red y con modelos ausentes/dañados usando perfiles temporales.
- [ ] Ensayar disco lleno/permisos; cierre y reinicio durante cada lote desde el paquete.
- [ ] Proteger main con test-windows/test-linux obligatorios y revisiones.
- [ ] Configurar aprobación manual del entorno de publicación y decidir firma del instalador.
- [ ] Aprobar explícitamente publicación. No anunciar compatibilidad de sistemas pendientes.

No hay garantía de ausencia absoluta de errores. La publicación sigue bloqueada mientras queden pérdida de datos, inicio, procesamiento o guardado sin resolver, y pruebas de los artefactos finales pendientes.

## Fixes históricos revisados

| Commit | Cobertura / criterio |
|---|---|
| fb58c42 Linux OCR y reinicio AppImage | test_package_selftest, test_settings_services; aceptación AppImage real pendiente |
| daf07a6 tamaño del asset Linux | test_linux_size; build CI valida tamaño |
| 8d16a09, d7b527e, aadfdc0 empaquetado Linux | Gate AppImage existente; ejecución de workflow pendiente |
| ca5ac79, 9aa0e62, 8a55073 elevación/log del actualizador | Flujo del instalador y UAC real pendientes; no se simula aceptación UAC como prueba de instalación |
| 84613c1 selectores Ajustes | test_settings_frame y test_settings_services |
| e790a83 rutas especiales y EXIF | test_convert, test_image_utils, test_metadata, test_write_safety |
| bfe629b Dock/macOS | macOS sigue experimental fuera de esta matriz; error de dependencias cubierto por test_remove_bg_frame |

Los cambios de empaquetado se verifican sobre artefactos: un test de texto YAML no demuestra que se instalen correctamente.

## Riesgos que siguen requiriendo aceptación

- El tipado está en basic; datos dinámicos de Pillow, OpenCV y modelos siguen dependiendo de contratos de esas bibliotecas.
- Los tests de temas/idiomas/escalas comprueban construcción y navegación. La legibilidad, el foco, teclado y cortes visuales necesitan inspección del paquete.
- Conversión CMYK, perfiles poco habituales y compresión con pérdida requieren muestras de referencia. No se atribuye equivalencia visual a todos los codecs.
- No se prueba pérdida de alimentación física ni errores de firmware/FS. La publicación atómica reduce escrituras parciales; no ofrece rollback del renombrado de un lote completo.
- En Linux, la publicación de outputs sin sobrescribir utiliza enlaces duros: un destino que no los soporte fallará de forma segura. Hay que comprobar carpetas locales, volúmenes externos y compartidos antes de declarar su compatibilidad.
- Bibliotecas de modelos, codecs, firmas/UAC y gestores de ventanas tienen aceptación separada por paquete y plataforma.
- Un trabajo global significa una instancia de la app; varias instancias pueden competir por cachés de modelos. Los outputs nuevos evitan sobreescrituras al publicar.

## Prueba breve desde el editor

1. Procesar tres imágenes y tratar de ejecutar un segundo lote; navegar y volver. La selección del módulo ocupado debe mantenerse y los controles recuperarse al terminar.
2. Cancelar selección y destino; editar/guardar EXIF sin cambios; cambiar solo autor en JPEG; probar TIFF multipágina. Ningún original debe perder contenido.
   En Metadatos, editar A, cargar B en «Ver» y guardar desde «Editar»: el editor debe seguir apuntando a A. En Paleta, seleccionar un archivo corrupto después de una foto válida debe conservar la paleta anterior.
3. Seleccionar A, luego B, limpiar y volver a seleccionar. La miniatura y el preview deben corresponder a la selección actual.
4. Cerrar/reiniciar durante un lote: cancelar mantiene la app; aceptar espera y luego cierra/reinicia.
5. Revisar los cinco idiomas, temas y escalas en la ventana más pequeña, con teclado, verificando foco y textos visibles.
6. Antes de publicar: repetir sobre instalador/portable/AppImage exactos en equipos limpios y con perfiles de prueba.

La corrida completa final registra **254 tests aprobados, cero omitidos, en 380,14 segundos**, incluidos los 15 casos de idiomas/escalas/temas. Son 97 tests más que los 157 registrados en la auditoría inicial. Ruff pasa y Pyright analiza las 92 fuentes de app sin skipunannotated, con cero diagnósticos. Las once mutaciones se detectaron. El build Windows y su preflight offline pasan; el hash de las fuentes coincide con el código final. Los checks remotos y la aceptación de equipos limpios siguen pendientes.
