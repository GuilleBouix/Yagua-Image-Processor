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
