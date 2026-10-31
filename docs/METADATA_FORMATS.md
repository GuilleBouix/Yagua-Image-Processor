# Metadatos EXIF: JPEG, TIFF, PNG y WebP

## Uso

Ver, Editar y Limpiar comparten hasta **100 imágenes**. La compatibilidad se
determina por el contenido real del archivo, no por su extensión:

| Formato | Ver y exportar EXIF | Editar y limpiar |
| --- | --- | --- |
| JPEG/JPG y TIFF/TIF | Sí | Sí, una sola imagen; se conserva la excepción de JPEG de cámara con previews MPO |
| PNG y WebP | Sí | Sí, estáticos |
| Otros formatos | No | No: «Formato no compatible. Usá JPEG, TIFF, PNG o WebP» |

Los formatos incompatibles conservan lista y preview. Las animaciones y archivos
multipágina de formatos compatibles pueden consultarse, pero no se modifican:
se informa el motivo sin descartar frames. Los errores de lectura se distinguen
de una imagen válida sin EXIF.

Se puede añadir EXIF a un PNG o WebP sin datos previos. Se utiliza el mismo
catálogo de autoría, cámara, captura, fechas, orientación y GPS de JPEG/TIFF.
El visor muestra únicamente las etiquetas conocidas que tienen datos; los ceros
válidos no se omiten. No es un editor de campos XMP o textos propios de PNG.

## Borradores y guardado

Abrir una fila permite inspeccionar la imagen; las casillas eligen los destinos.
Completá los campos de la imagen abierta y pulsá **Guardar…**. Una sola ventana
permite elegir **Solo esta imagen** o **A las N imágenes seleccionadas**, o cancelar.
La elección aplica y guarda los campos con contenido; los vacíos no borran ni
reemplazan datos. Se incluyen los valores que ya tenía la imagen abierta, no sólo
los recién escritos. Para conservar un valor individual en todo el lote, dejá ese
campo vacío antes de guardar. Las casillas determinan los destinos; abrir una fila
sólo cambia la imagen inspeccionada.

El botón ocupa todo el ancho. Ya no hay botón ni ventana de Copiar campos, ni una
segunda confirmación para guardar una edición. Si se eligió sobrescribir, el
aviso está en esa misma ventana y la acción del lote indica su cantidad. Para
copias, después de elegir el alcance se pide la carpeta; cancelar ese selector
permite volver a elegir el alcance sin aplicar cambios a otros borradores.
Borrar GPS, sincronizar fechas y transformar orientación mantienen sus acciones
explícitas. Los borradores independientes se conservan: los campos con contenido
del formulario prevalecen en los destinos elegidos, y los demás cambios propios
de cada imagen permanecen.

Crear copias es la opción inicial. Sobrescribir originales requiere confirmar.
Se conservan nombres, numeración de conflictos, cancelación, escrituras atómicas,
verificación de cambios externos y borradores independientes. Al crear copias se
conservan los originales y sus borradores; al sobrescribir se recargan los datos
y se invalida la caché. Un formato incompatible se omite y se informa por archivo,
sin frenar los demás ni crear una copia falsa.

Editar PNG reemplaza su bloque `eXIf` sin cambiar los bloques comprimidos de
píxeles (`IDAT`), la paleta o la transparencia. Editar WebP reemplaza `EXIF` y
actualiza la cabecera del contenedor sin recodificar `VP8`, `VP8L` o `ALPH`.
Los demás metadatos y perfiles de color se conservan. Se comprueban longitudes,
CRC de PNG, framing RIFF y las restricciones de una sola imagen antes de escribir.
Un contenedor dañado no se publica sobre el original.

## Limpieza y orientación

En PNG, Limpiar elimina `eXIf`, `tEXt`, `zTXt`, `iTXt` —incluido XMP— y `tIME`.
En WebP elimina `EXIF` y `XMP ` y ajusta sus indicadores en `VP8X`. Conserva el
perfil ICC y la información de color y transparencia. Las reglas de limpieza de
JPEG/TIFF se mantienen.

Si la orientación exige girar o reflejar píxeles, Limpiar conserva la apariencia
aplicándola antes de eliminar EXIF. La acción explícita de orientación del editor
también normaliza la etiqueta a 1. Estas transformaciones guardan PNG sin pérdidas
y WebP sin pérdidas adicionales respecto a los píxeles decodificados, conservando
alfa. **Pueden aumentar el peso**, especialmente en WebP originalmente con pérdida.

## Exportación y errores

TXT/JSON mantienen las claves y estructura actuales. La exportación conjunta
registra cada ruta y sus metadatos; los incompatibles llevan
`error: "meta_format_unsupported"`, en vez de aparecer como imágenes sin EXIF.
Una lectura dañada se identifica como error. Los detalles por archivo permiten
ver qué se guardó, qué se omitió y qué falló.

## Implementación y pruebas

Pillow 12.1.1 y piexif 1.1.3 existentes; sin dependencias nuevas. Las transformaciones
de PNG de 16 bits en color utilizan OpenCV y NumPy ya incluidos para conservar
sus muestras de 16 bits, que Pillow reduciría a 8 bits al decodificar RGB/RGBA. Las firmas públicas
se mantienen. Los helpers internos de contenedores aíslan la lectura y escritura
de bloques; los workers siguen devolviendo datos simples y Tk se actualiza en el
hilo principal. Se mantienen virtualización, caché y descarte de cargas antiguas.

La cobertura incluye Unicode, ceros, fracciones, GPS, archivos sin EXIF, paletas,
PNG de 16 bits, WebP con/sin pérdida, transparencia, perfiles, orientación,
contenedores dañados, animaciones, TIFF multipágina, lotes mixtos, copias,
sobrescritura y exportaciones. El autotest de paquetes también comprueba edición
EXIF y conservación de píxeles y perfiles en los cuatro formatos.

```bash
python scripts/verify.py -q tests/modules/test_metadata.py tests/modules/test_metadata_batch.py tests/modules/test_metadata_view.py tests/modules/test_metadata_containers.py tests/ui/test_metadata_collection.py tests/ui/test_metadata_frame.py tests/ui/test_metadata_view_frame.py
```

En Ubuntu, usar Python 3.13 y anteponer `xvfb-run -a` para las pruebas de interfaz.
El script usa preferencias temporales y bloquea la red de las pruebas.

## Validación local — 2026-10-31

- Windows, Python 3.13.13 y Pillow 12.1.1: **366 pruebas relacionadas aprobadas**.
- Ubuntu WSL2/Xvfb, Python 3.13.17 y Pillow 12.1.1: **366 pruebas relacionadas aprobadas**.
- Se repitieron las 35 pruebas de contenedores y las 22 de estados/compatibilidad
  y geometría tras los últimos ajustes. Las suites incluyen nueve idiomas,
  MPO, guardado seguro y controles compartidos. No se ejecutó la suite completa
  de toda la app ni se construyeron paquetes de distribución.
- Ruff, Pyright y comprobación del diff: aprobados. El autotest de formatos del
  paquete se ejecutó desde fuente en ambos sistemas y aprobó los nueve formatos
  existentes, incluidos los nuevos round trips EXIF PNG/WebP.
- Se comprobó la geometría de las tres pestañas para JPEG, PNG y WebP con ventanas
  grandes y 900×600 y escalas 100/75/50 %. Se inspeccionaron capturas de edición
  y del estado de formato incompatible. Los informes JUnit quedan en
  `reports/metadata-png-webp-windows.xml` y `reports/metadata-png-webp-linux.xml`.
- Las suites emitieron siete avisos de Pillow sobre EXIF en los casos de lectura
  de fixtures; no produjeron fallos. WSL/Xvfb no sustituye la aceptación del
  AppImage en un escritorio limpio.

## Guardado simplificado — validación 2026-10-31

Se retiró la ventana de copiar campos. Guardar permite elegir la imagen abierta
o las seleccionadas y aplica todos los campos con contenido. La confirmación de
sobrescritura está integrada en esa elección; no hay una segunda ventana de
confirmación para las ediciones. Los campos vacíos mantienen los datos anteriores.

- Windows/Python 3.13.13 y Ubuntu WSL2/Xvfb/Python 3.13.17: **372 pruebas
  relacionadas aprobadas por sistema**, con los mismos siete avisos de Pillow.
- Se comprobaron imagen abierta frente a selección, campos ya existentes,
  campos vacíos, borradores independientes, exclusión de imágenes sin marcar,
  copias, sobrescritura, cancelación del diálogo y de la carpeta, snapshots del
  worker y ausencia de una segunda confirmación. Ruff y Pyright aprobados.
- Se procesaron los 80 JPEG/TIFF/PNG/WebP del lote facilitado por el usuario,
  usando únicamente copias en una carpeta temporal, en ambos sistemas:
  **79 guardados, 1 sin cambios y 0 errores**. Se verificaron los valores guardados
  y los hashes SHA-256 de todos los originales antes y después: intactos.
- Informes: `reports/metadata-save-scope-windows.xml` y
  `reports/metadata-save-scope-linux.xml`. No se hicieron builds de distribución.
