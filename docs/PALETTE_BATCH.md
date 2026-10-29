# Paletas por lotes / Batch palettes

Esta guía describe el código actual; los paquetes anteriores pueden conservar
la selección individual. No anuncia una nueva release.

## Uso

La vista usa una sola columna: selección de imágenes, paleta con valores,
lista de archivos y acciones de guardado al final.

- **Agregar imágenes** incorpora archivos a la colección actual, hasta 100.
  No repite rutas. Al alcanzar el límite lo informa; si hay exceso o duplicados,
  muestra cuántos quedaron fuera. Limpiar vacía la colección y sus resultados.
- La primera imagen se abre automáticamente. Hacer clic en otra fila cambia la
  paleta visible, sin reducir el lote. Las miniaturas y las filas se reutilizan.
- Elegir **4, 6, 8, 10 o 12** colores calcula la paleta de la imagen abierta.
  Una imagen con pocos colores puede devolver menos de los solicitados.
  HEX, RGB, HSL y CSS var copian el valor correspondiente.
- **Guardar todas** calcula las paletas pendientes con la cantidad elegida.
  Trabaja secuencialmente en segundo plano, muestra progreso
  y continúa si un archivo falla. La fila afectada conserva un aviso breve;
  el pie muestra únicamente el total procesado o guardado y los errores.
- **Guardar paleta** exporta la imagen abierta mediante el diálogo de archivo.
  **Guardar todas** pide una carpeta y genera un PNG por imagen, por ejemplo
  `playa_paleta.png`. Nombres existentes se numeran (`playa_paleta_1.png`).
  No reemplaza archivos del lote. Cancelar el diálogo no escribe archivos.
  Si una exportación falla, conserva las que ya terminaron.
- Los píxeles completamente transparentes no aportan colores. Los parcialmente
  transparentes aportan su RGB sin mezclarlo con un fondo. Una imagen totalmente
  transparente muestra «La imagen no tiene colores visibles». Los archivos
  dañados o animados/multipágina no admitidos muestran un error por archivo.

## Implementación

`app/modules/palette.py` conserva las funciones individuales y añade una opción
de publicación sin reemplazo a la exportación. `palette_batch.py` separa los
servicios por lote de Tk: caché, firmas de archivo, extracción y exportación.
La caché retiene hasta 500 resultados pequeños (100 archivos × 5 cantidades),
sin conservar imágenes completas. Comprueba tamaño, modificación, cambio de
archivo e identidad antes y después de cada extracción; una nueva revisión
invalida los colores anteriores. Guardar vuelve a comprobar la fuente.

La selección usa un trabajador con una extracción en curso y sólo la solicitud
pendiente más reciente. Limpiar, cambiar de imagen/cantidad y cerrar invalidan
las respuestas antiguas. La decodificación y cuantización quedan fuera de Tk;
las imágenes de Tk, filas y colores se actualizan en el hilo principal. La
construcción sigue siendo incremental. Las muestras de color se reutilizan y
se pueden desplazar horizontalmente en ventanas estrechas.
Las muestras usan controles CTk escalables, igual que sus botones: al 50% no
conservan una altura física fija que corte la fila «CSS var». Se verifica que
todos los botones queden dentro de la preview para 4/6/8/10/12 colores.

Las exportaciones se publican atómicamente. Se reservan las rutas del lote y
las salidas previas, y se reintenta otro nombre si aparece un conflicto durante
la publicación. Un fallo no deja un PNG incompleto como resultado final.

## Validación

Windows, Python 3.13, con preferencias temporales y red bloqueada:

```powershell
python scripts/verify.py -q tests/modules/test_palette.py tests/modules/test_palette_batch_core.py tests/ui/test_palette_frame.py tests/ui/test_palette_batch.py tests/ui/test_ui_fluency.py tests/ui/test_operations.py tests/ui/test_startup.py tests/test_translations.py
python -m ruff check app tests/modules/test_palette_batch_core.py tests/ui/test_palette_frame.py tests/ui/test_palette_batch.py
python -m pyright --pythonpath .venv/Scripts/python.exe
git diff --check
```

En Ubuntu con Python 3.13, usar el mismo comando de pruebas precedido por
`xvfb-run -a`. Las pruebas cubren 1/100/más de 100 imágenes, cargas sucesivas,
duplicados, revisiones de caché, alfa, archivos ilegibles, errores parciales,
nombres iguales, fuentes protegidas, cancelación y respuestas tardías.
La interfaz se comprueba en 1400×900 y 900×600, a 100/75/50 %.

La lista compartida conserva el rango de desplazamiento sin crear una superficie
del alto de todo el lote. Esto corrige el `X Error: BadAlloc` de Xvfb en listas
largas. Las comprobaciones se ampliaron a 500 y 5.000 filas, con desplazamiento
en ambos sentidos y tamaño físico acotado, sin retirar las aserciones originales.
También se comprueba que las muestras llenen el ancho al pasar de 12 colores
a 4, 6, 8 o 10, reutilizando los mismos controles.

Los resultados de la ronda actual y las versiones exactas del entorno se
registran en [validación local](VALIDATION_2026_10_29.md). La aceptación visual
manual del usuario y la validación de paquetes compilados son comprobaciones
separadas de estas pruebas de código fuente.

## English quick guide

Add up to 100 unique images, then click a row to inspect its palette. The first
image opens automatically. Color count changes affect the open image.
**Save all** calculates missing palettes
and writes one collision-safe `<name>_paleta.png` per image. **Save palette**
exports only the open image. Fully transparent pixels are ignored; partially
transparent pixels contribute their RGB without an artificial background.
An unreadable or entirely transparent image does not stop the batch. Clearing
the collection invalidates pending replies and releases cached colors.
