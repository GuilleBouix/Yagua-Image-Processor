# Previews y ajustes de Quitar Fondo

Describe el código fuente de `main` preparado para Yagua 2.0. Los paquetes de
prueba anteriores pueden no incluir estos controles. No anuncia una release.

## Uso

### Redimensionar, Recortar y Canvas

- La primera imagen se abre automáticamente. Hacer clic en una fila cambia la
  imagen inspeccionada, **sin reducir el lote que se va a procesar**.
- El panel derecho muestra el resultado de la pestaña visible y las dimensiones
  originales y finales, después de corregir la orientación EXIF.
- Redimensionar respeta porcentaje, píxeles, presets y conservación de proporción.
  Mantener proporción usa el ajuste dentro de los límites actuales, sin ampliar.
- Recortar conserva el recorte centrado existente; la preview no incorpora un
  editor para arrastrar o desplazar el área de recorte.
- Canvas mantiene la imagen centrada y la reduce si excede el lienzo. Sus sliders
  de ancho y alto están sincronizados con los inputs y empiezan en 1080 × 1080 px.
  El rango inicial es 1–8192 px; un valor manual mayor amplía el rango del slider.
  Esto no elimina los límites de memoria al guardar una imagen real grande.
- Los valores incompletos o inválidos ocultan el resultado anterior y muestran
  una indicación. Cambiar parámetros no escribe archivos.
- El damero representa transparencia; no se añade al archivo de salida. Canvas
  conserva la política de transparencia y formatos del procesamiento existente.

La preview usa píxeles reducidos. Permite revisar geometría y composición, pero
no representa una inspección del detalle o la compresión final a escala 1:1.
El lote conserva su límite de 100 imágenes.

### Quitar Fondo

El panel muestra **Original** al cargar y **Resultado** después de procesar y
guardar correctamente. Lee la salida publicada en disco, sin ejecutar otra
inferencia. Cada fila conserva la asociación con su salida; si falla una imagen,
se muestra su original y el error. El lote conserva su límite de 10 imágenes.

Los tres ajustes están siempre visibles:

| Ajuste | Valores | Inicial | Efecto |
| --- | --- | --- | --- |
| Refinar bordes | Auto / Sí / No | Auto | Auto mantiene la limpieza de máscara y activa alpha matting en fondos claros uniformes; Sí solicita ambos en cualquier fondo; No desactiva ambos. |
| Reducir halo blanco | 0–100 % | 85 % | Atenúa contaminación de color en bordes semitransparentes próximos al color del fondo claro detectado. En fondos no clasificados como claros uniformes no se aplica. |
| Contraer / expandir | −5 a +5 px | 0 px | Negativo contrae la máscara, positivo la expande; se mide en píxeles de la imagen original, no de la preview. |

La reducción de halo es independiente del selector de refinado. Al expandir se
recupera el color original de los píxeles expuestos, para evitar bordes negros
causados por colores transparentes vacíos. Expandir también puede revelar fondo;
contraer puede eliminar detalles finos. Ningún ajuste garantiza recuperar un
detalle que el modelo haya identificado incorrectamente.

La salida conserva transparencia y los formatos PNG, WebP y TIFF. No hay selector
de color de fondo ni sección desplegable de ajustes. Cambiar controles después
de guardar conserva el resultado guardado en la preview y muestra que hace falta
volver a procesar. No se modifica una salida al mover un slider.

Los valores iniciales conservan el pipeline anterior. No se añaden modelos,
dependencias, descargas ni proveedores de ejecución. El refinado puede consumir
más CPU, memoria y tiempo; los lotes siguen procesándose secuencialmente.

## Implementación

- `app/modules/resize_geometry.py` comparte el redondeo, cálculo de dimensiones,
  recorte y posición del lienzo entre guardado y preview. Mantiene el redondeo de
  `Pillow.thumbnail`, incluida la prohibición de ampliar al conservar proporción.
- `app/ui/preview.py` contiene `LivePreview` y el render de píxeles. Carga RGBA
  reducida de la caché compartida de 64 MiB y renderiza hasta 1024 × 1024 px. No
  crea un lienzo con las dimensiones completas solicitadas por Canvas.
- Cada preview tiene como máximo un worker activo. Las revisiones descartan
  respuestas antiguas; los cambios de Redimensionar se agrupan durante 150 ms.
  Decodificación, transformaciones y damero corren fuera de Tk. Las imágenes CTk
  y las actualizaciones de widgets se crean en el hilo de interfaz.
- `StableRender` espera dos medidas iguales separadas por 16 ms. El viewport
  reserva su espacio y usa `place` para la imagen, que no participa en el tamaño
  solicitado al layout. La preparación de altura del workspace es optativa y
  ocurre antes de renderizar, para evitar conservar una altura inicial obsoleta.
- Ocultar el módulo suspende renders y cancela timers. Un worker ya iniciado
  puede terminar, pero su resultado obsoleto no se aplica. Limpiar, recargar o
  cerrar invalida las solicitudes anteriores. No se precargan previews del lote.
- `FileList.on_select` es opcional; las demás vistas mantienen su comportamiento.
  Las filas virtualizadas se reutilizan y sólo la imagen activa recibe preview
  grande. Un callback puede devolver `False` para rechazar cambios durante un
  procesamiento bloqueado.
- Quitar Fondo asocia `ruta_entrada` con `ruta_salida` de cada fila `saved` del
  resultado del guardado. Usa `path_key` para reconocer `/`, `\` y mayúsculas de
  Windows como la misma entrada. Las sobrescrituras invalidan la caché; las
  copias conservan el original. El guardado atómico y sus confirmaciones siguen
  siendo compartidos con el resto de la app.

### Contrato de procesamiento

`quitar_fondo` y `batch_quitar_fondo` aceptan el nuevo parámetro opcional de sólo
palabra clave `config: RemoveBgConfig | None`. Las llamadas anteriores y las
claves de sus resultados se conservan. `None` usa los valores iniciales.

`RemoveBgConfig` es inmutable. Añade `refine_edges` (`auto`, `on`, `off`),
`halo_strength` (entero 0–100) y `edge_offset` (entero −5–5). Valores fuera del
contrato se rechazan antes de procesar. La UI captura la configuración antes de
confirmar el guardado y el worker no lee variables de Tk. Si se utiliza el modelo
de respaldo, se conserva la configuración y sólo cambia la identidad del modelo.

Orden del pipeline: análisis del fondo, segmentación/refinado solicitado,
ajuste de contorno, reducción de halo claro y guardado. Los refinamientos
posteriores usan Pillow y NumPy existentes.

## Validación y reproducción

Las dependencias de CI están fijadas en `requirements.txt`,
`requirements-linux-cpu.txt` y `requirements-dev.txt`; no se modificaron para
esta funcionalidad. CI utiliza Python 3.13.17, Windows y Ubuntu 22.04/Xvfb.

En Windows, con el entorno activado:

```powershell
python -m pip check
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath (Get-Command python).Source app
python scripts/ci/check_licenses.py --installed
python -m scripts.ci.preflight --version 2.0.0 --platform windows
python scripts/ci/partitions.py
python scripts/verify.py -q --ignore=tests/ui
python scripts/verify.py -q tests/ui
```

En Linux, instalar `requirements-linux-cpu.txt` y `requirements-dev.txt` y usar
las mismas comprobaciones de calidad. Ejecutar:

```bash
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m scripts.ci.preflight --platform linux
python scripts/ci/partitions.py
xvfb-run -a python scripts/verify.py -q --ignore=tests/ui
xvfb-run -a python scripts/verify.py -q tests/ui
```

`scripts/verify.py` usa preferencias temporales y bloquea las solicitudes HTTP de
la suite. El preflight Linux sin `--version` comprueba materiales locales sin
consultar tags; con versión también valida su disponibilidad en GitHub y requiere
el contexto de Actions correspondiente.

Las pruebas específicas comparan geometría y píxeles de imágenes pequeñas con
salidas reales; cubren EXIF, alfa, lienzos grandes con preview acotada, sliders,
inputs inválidos, cargas sucesivas, errores de lectura, respuestas tardías y vistas
ocultas. También cubren modos de refinado, halo, contorno, valores inválidos,
configuración capturada y guardado con copias o sobrescritura.

La aceptación visual debe comprobar ventana grande y 900 × 600, escalas 100/75/50 %,
selección de filas y las tres pestañas. En ancho reducido los paneles se apilan y
puede ser necesario desplazar la vista. Probar un lote de 100 en Redimensionar y
uno de 10 en Quitar Fondo; rechazar el exceso conserva los límites anteriores.

Una suite local aprobada valida el código fuente. Los nuevos instaladores,
portable y AppImage se verificarán por separado mediante el flujo de candidatos
descrito en [CI_RECOVERY.md](CI_RECOVERY.md), antes de anunciar una prueba pública.
