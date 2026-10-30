# Fotos JPEG con vistas previas MPO

Algunas cámaras guardan dentro de un `.JPG` la foto principal y una vista previa
JPEG adicional. Pillow identifica ese contenedor como MPO y lo considera animado,
aunque las imágenes adicionales sean solo vistas previas. La protección general
contra archivos multipágina rechazaba también esas fotos.

## Qué acepta Yagua

La validación compartida permite exclusivamente un MPO con la foto principal al
inicio y las demás entradas identificadas expresamente como miniaturas VGA/Full
HD, con dimensiones inferiores a la principal. Los MPO estéreo, panorámicos, de
tipo desconocido o con vistas previas ilegibles siguen bloqueados, igual que las
animaciones GIF/APNG/WebP y los TIFF multipágina. No se decide por la extensión.

Convertir, Comprimir, Redimensionar, Recortar, Canvas, Marca de agua, Quitar Fondo
y Metadatos trabajan con la foto principal. El formato de salida equivalente es
JPEG cuando se conserva el formato. En Metadatos, estos archivos también permiten
editar los campos EXIF. El guardado que solo modifica EXIF extrae el JPEG principal
y retira su índice MPF sin recomprimir los píxeles.

Paleta, OCR, LQIP y las previews inspeccionan la foto principal. La lectura y la
extracción no modifican el original. Renombrar sigue moviendo el archivo completo,
incluidas sus vistas previas, sin transformar su contenido.

## Aviso y seguridad

Las confirmaciones compartidas de guardado incluyen, una sola vez por lote:

> Se usará la foto principal. El archivo guardado no conservará las vistas previas
> de la cámara.

El aviso se muestra antes de escribir, tanto en copias como en sobrescritura.
Cancelar conserva todo. En copias se conserva el MPO original; al sobrescribir se
reemplaza por el resultado sin las vistas previas. No se trasladan índices MPF que
apuntarían a imágenes que ya no están en el resultado. Se mantienen las reglas
existentes de orientación, perfiles de color, EXIF y compresión sin aumento de peso.

`app/utils/image_source.py` concentra la identificación y la extracción sin
recompresión. `require_single_frame` conserva su firma pública y utiliza esa
identificación. Los planes de salida agregan el campo opcional
`embedded_previews`, cuyo valor predeterminado es cero, para informar a la UI sin
releer imágenes en el hilo de Tk. No hay dependencias nuevas.

## Pruebas

Los fixtures se generan con una foto roja y una miniatura verde para detectar si
se procesa la imagen equivocada. Se cubren orientación EXIF, copias y sobrescritura,
metadatos sin recompresión, selección de la principal en OpenCV/OCR y Quitar Fondo,
cancelación del aviso, MPO de otros tipos, miniaturas truncadas y archivos animados
o multipágina. Las fotografías del usuario no forman parte del repositorio.

### Comprobación con archivos reales — 30 de octubre de 2026

En Windows y Ubuntu WSL2 se procesaron los siete archivos indicados del escritorio:
seis seguían siendo MPO con foto de 5456×3064 y preview de 1920×1080; `principal.JPG`
ya era un JPEG normal de 2048×1150 al realizar la comprobación.

| Operación, por sistema | Guardados | Sin mejora | Errores |
| --- | ---: | ---: | ---: |
| Convertir a WebP, calidad 90 | 7 | 0 | 0 |
| Convertir a JPEG, calidad 90 | 6 | 1 | 0 |
| Comprimir, calidad 85 y EXIF conservado | 7 | 0 | 0 |

Se verificaron formato, dimensiones, lectura completa de las salidas y hashes
inalterados de los originales. Una de las fotos MPO también pasó por Redimensionar,
Recortar, Canvas, Marca de agua, edición y limpieza de EXIF, Paleta y LQIP. OCR y
Quitar Fondo se ejecutaron con los modelos reales ya descargados, con red bloqueada:
la foto no produjo texto OCR y el resultado de Quitar Fondo tenía alfa entre 0 y 255.
Renombrar se comprobó sobre una copia, conservando exactamente sus bytes.

Las suites se ejecutan con `scripts/verify.py`, perfiles temporales y red externa
bloqueada. En WSL se usa Python 3.13.17 con el módulo local de Tk 8.6 preparado para
Xvfb. El Tk 9 de ese intérprete standalone carece del registro de fuentes que exige
la suite; no se cambia el código de fuentes para adaptar la app a ese entorno.

Resultados locales: Windows, 1098 aprobadas y una omisión de plataforma; Ubuntu,
1100 aprobadas. Los dos últimos controles del reconocimiento MPO se verificaron
además en una ejecución final de sus 31 casos específicos por sistema. Ruff,
Pyright y la revisión del diff pasaron. Los avisos de EXIF corrupto de la suite
corresponden a sus fixtures de metadatos dañados, no a las fotos procesadas.
