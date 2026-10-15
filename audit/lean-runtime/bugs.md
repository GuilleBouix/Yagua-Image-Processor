# Hallazgos ajenos a la reducción de dependencias

## OCR: primera descarga desde salida CP1252 en Windows

Estado: corrección autorizada por el usuario e implementada, con regresión.

Se reproduce en la base `1914a11` y en el entorno nuevo: `EasyOCR.Reader`
descarga CRAFT con una barra de progreso que imprime `█`. Si stdout usa
CP1252, lanza `UnicodeEncodeError` y la descarga no termina. No depende de
quitar paquetes ni de cambiar OpenCV. Se observó con salida redirigida del
ejecutable en CI y con Python desde consola local.

El verificador optativo configura su propia salida en UTF-8 para poder
continuar la comparación sobre la misma instrumentación. Eso no corrige el
flujo normal de la app ni certifica este escenario de consola.

Corrección: desactivar exclusivamente la barra de progreso de la
biblioteca en la carga de OCR; mantener el estado de carga que ya presenta
la interfaz y los mismos modelos, parámetros y calidad. Agregar una
regresión con una salida CP1252. La comprobación con modelos reales forma
parte de la validación de paquetes online/offline.

## Convertir: pérdida del perfil ICC en JPEG y WebP

Estado: corrección autorizada por el usuario e implementada, con regresiones.

Una imagen JPEG sintética con un perfil sRGB de 588 bytes pierde ese perfil
al convertirse a JPEG o WebP. PNG, AVIF, HEIC y TIFF lo conservan en la misma
prueba. `app/modules/convert.py` no cambió entre `1914a11` y la reducción:
el fallo es previo y no lo produce OpenCV headless.

La pérdida de un perfil distinto de sRGB puede cambiar la interpretación
del color en visores. Se consultó conservar explícitamente el ICC al
guardar JPEG/WebP, con regresiones, antes de modificar ese comportamiento.

Se captura el perfil RGB antes de preparar la imagen, incluida la composición
de transparencia sobre blanco para JPEG, y se entrega explícitamente al encoder.
Se comprueba mediante relectura del archivo; la fotografía de entrada no cambia.
El paquete candidato exige conservarlo. La comparación histórica registra la
pérdida de la base como un fallo conocido, sin modificar su código de conversión.

Límite previo conservado: la normalización CMYK/gris a RGB sigue usando Pillow
sin gestión de color. No se copia un perfil CMYK/gris sobre píxeles RGB porque
sería incorrecto; la conversión gestionada de esos espacios requiere otro alcance.
