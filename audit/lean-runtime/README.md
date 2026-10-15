# Runtime reducido — Yagua

Rama: `codex/lean-runtime`. Base de comparación: `1914a11`.

## Política

- `requirements.txt`: ejecución, 51 dependencias comunes y dos específicas de Windows; un solo OpenCV, headless 4.13.0.92.
- `requirements-dev.txt`: pytest, cobertura, Ruff y Pyright. Entorno separado.
- `requirements-build.txt`: PyInstaller y sus herramientas. Entorno separado del de tests y del editor.
- Linux conserva Torch/Torchvision CPU explícitos. No se cambian motores, modelos, parámetros de calidad ni formatos.
- Se retiran 44 entradas ajenas a la ejecución, seis pasan a desarrollo y cinco a construcción. Lista exacta: [dependencies.json](dependencies.json).
- Se conservan Torch, Torchvision, ONNX Runtime, NumPy, SciPy, Numba, llvmlite y PyMatting. No se recortan sus módulos internos ni DLL/SO arbitrarias.
- Los imports estáticos resuelven la API y las sesiones de rembg. Se excluyen sus comandos/CLI; se conserva su registro de sesiones completo, porque el paquete lo importa al inicializar.
- Torch conserva todos sus módulos y bibliotecas. Se excluyen exclusivamente sus ejecutables de pruebas C++ y el compilador Protobuf; permanece `torch_shm_manager`.
- Windows conserva TBB 2022.3.1 y fija su dependencia tcmlib en la versión 1.5.0 que resolvía la base. Numba enlaza `tbb12.dll`; retirarlo cambia su backend de ejecución. En Linux la base no incluía `libtbb.so.12` y se conserva su backend OpenMP. La comparación exige el mismo backend en ambos paquetes. Se incluyen también los avisos de terceros que los wheels de Intel instalan fuera de `dist-info`.
- EasyOCR conserva código/configuración compartidos, CRAFT, reconocimiento inglés y latino. Solo se empaquetan recursos de idiomas español/inglés: son las opciones actuales de OCR, independientemente del idioma de la interfaz.
- Recursos del instalador y macOS quedan en el repositorio. Fuentes, iconos de la app, licencias, metadatos y codecs permanecen en el paquete.
- La DLL `opencv_videoio_ffmpeg*` es exclusivamente de video. Su exclusión se comprueba con imports nativos, los nueve formatos y OCR real en el ejecutable.
- Linux: la inspección de dependencias ELF encontró cero consumidores de GTK, OpenGL, Mozilla NSS, GLib, SM/ICE y xkbcommon en el paquete de la app ni en su cierre de dependencias. Se retiran esas raíces de la receta; la evidencia previa está en [linux-native-before.json](linux-native-before.json). Se conservan X11/Xext/Xrender, fuentes, OpenMP y las dependencias de Tk. FFmpeg y OpenBLAS de OpenCV en Linux sí están enlazados y permanecen.

Quitar una dependencia del entorno no implica ahorrar su tamaño completo en el ejecutable: algunas ya no se empaquetaban. El ahorro se informa mediante archivos reales.

## Modelos y uso local

La primera ejecución de cada opción descarga sus modelos. Las siguientes usan los mismos archivos sin red:

1. `craft_mlt_25k.pth`: detección OCR.
2. `english_g2.pth`: reconocimiento inglés.
3. `latin_g2.pth`: español y español+inglés.
4. `isnet-general-use.onnx`: quitar fondo, principal.
5. `u2netp.onnx`: fallback de compatibilidad.

No se incorporan pesos al ejecutable ni se cambia la ubicación habitual de los modelos del usuario. Los verificadores usan perfiles, modelos y cachés temporales.

## Verificación reproducible

El workflow `Lean runtime validation (no publication)` solo valida. Tiene permiso de lectura, no usa acciones de release y no crea tags.

Instalación, Ruff, Pyright y tests tienen pasos separados. Se reutiliza solamente
la caché de descargas de pip; cada entorno virtual sigue siendo nuevo. Pip y apt
reintentan sus descargas, manteniendo los errores de dependencias o tests como
fallos. No se reintentan ni se omiten comprobaciones funcionales para obtener verde.

`summary.md` y `comparison.json/checks` identifican cada bloqueo: paquete base,
paquete candidato, total instalado, píxeles o backend Numba. `diagnostics.json`
registra los pasos incluso si falla la instalación, y se conserva el log de Xvfb.
`saved_bytes` positivo significa ahorro; el límite bloqueante se aplica al total
absoluto de app + modelos + cachés. No se añade ningún bypass por variable de
entorno ni `continue-on-error` a estos controles.

En cada plataforma:

1. Entorno de tests nuevo: instalación y `pip check`, Ruff, Pyright y suite completa, con Tk obligatorio.
2. Construcción de la base y del candidato, secuencialmente en el mismo runner y con entornos nuevos. El único cambio sobre la base es el mismo verificador optativo que usa el candidato; su lógica, requisitos y especificación originales se conservan. La base registra como fallo conocido la pérdida previa de ICC en JPEG/WebP; el candidato debe conservar los perfiles RGB. La instrumentación configura su salida UTF-8 para poder comparar la base con el bug previo de CP1252. Las dos correcciones de la app fueron autorizadas y figuran en [bugs.md](bugs.md).
3. Linux construye AppImage y verifica su runtime y la extracción. Windows construye la carpeta portable y ZIP.
4. Tres arranques con dibujo de la pantalla inicial, sin red. Se registra tiempo total del proceso, incluido arranque y cierre.
5. Pruebas online con descarga, luego en un proceso nuevo con sockets bloqueados: español, inglés, ambos; modelos principal y fallback; transparencia, nueve formatos, orientación, píxeles/ICC/EXIF; navegación de todos los módulos, portapapeles y exportación TXT. Los SHA256 de los modelos deben conservarse. Las nueve conversiones y ambos resultados de quitar fondo deben decodificar a los mismos píxeles que la base; Numba debe conservar el mismo backend.
6. Se registran carga de modelos, procesamiento, tiempo y pico de memoria residente del proceso por etapa. Es un pico acumulado, no memoria exclusiva de esa etapa. La descarga online depende de la red; comparar las etapas offline para tiempos de carga/procesamiento.
7. Inventario congelado: módulos prohibidos, recursos OCR, DLL de video y recursos ajenos a la plataforma.

Los procesos de verificación reciben un perfil de usuario, carpetas de fuentes,
preferencias y temporales propios antes de importar Tk; también se incluyen esas
cachés en la medición. No se modifica el perfil real del editor.

Numba 0.64 puede ignorar `NUMBA_CACHE_DIR` al cargar módulos congelados sin
archivo fuente y consultar las carpetas conocidas de Windows. El verificador
redirige también ese fallback dentro de su propio proceso, antes de importar
PyMatting, y exige encontrar cachés `.nbc` en el perfil medido. La ubicación de
cache de la app normal no cambia. Las mediciones anteriores a este ajuste son
preliminares y no se usan como resultado final.

Desde el repositorio, con Python 3.13:

```powershell
python scripts/ci/validate_lean_runtime.py --reports lean-reports
```

Linux requiere las dependencias nativas listadas en el workflow y ejecuta las pruebas gráficas con Xvfb. Los entornos temporales de cada construcción se liberan al terminar; los informes quedan en la carpeta indicada.

## Medición y límite

Máximo autorizado: **2.000.000.000 bytes** (2 GB decimales); el check exige quedar
por debajo de ese valor. El objetivo inicial de 1.500.000.000 bytes se conserva
como referencia de optimización. Se suma el tamaño lógico de archivos regulares de:

- App portable descomprimida en Windows / AppImage extraído completo en Linux.
- Los cinco modelos y recursos que descargan sus bibliotecas.
- Cachés persistentes de ejecución y perfil generado por las pruebas.

El ZIP/AppImage comprimido se informa aparte. No se cuentan los entornos de desarrollo/construcción, imágenes temporales usadas en pruebas ni informes. No se suman componentes solapados ni se cuentan dos veces los enlaces simbólicos internos.

`scripts/ci/check_installed_size.py` rechaza el total fuera del límite y enumera los archivos más pesados. Los workflows de release aplican este control después de los tests online/offline y antes de publicar. Un control preliminar del paquete por sí solo no certifica el total instalado.

## Resultados

Construcciones comparativas del 15/10/2026, base `1914a11` y candidato `414e953`.
Ejecución: [validación sin publicación](https://github.com/GuilleBouix/Yagua-Image-Processor/actions/runs/38784574599).
Datos completos: [Windows](windows.json) y [Linux](linux.json).

Tamaños lógicos en bytes; modelos y cachés se suman al paquete descomprimido.

| Sistema | Componente | Antes | Ahora | Ahorro |
|---|---|---:|---:|---:|
| Windows | App | 897.579.619 | 799.498.805 | 98.080.814 |
| Windows | Cinco modelos | 296.925.337 | 296.925.337 | 0 |
| Windows | Cachés | 5.633.070 | 5.633.330 | -260 |
| Windows | **Total instalado** | 1.200.138.026 | 1.102.057.472 | 98.080.554 |
| Windows | ZIP | 331.187.897 | 289.684.789 | 41.503.108 |
| Linux | App | 1.407.757.758 | 1.224.416.980 | 183.340.778 |
| Linux | Cinco modelos | 296.925.337 | 296.925.337 | 0 |
| Linux | Cachés | 6.204.362 | 6.204.818 | -456 |
| Linux | **Total instalado** | 1.710.887.457 | 1.527.547.135 | 183.340.322 |
| Linux | AppImage | 392.463.552 | 341.374.144 | 51.089.408 |

**Windows y Linux cumplen el máximo actual de 2 GB**, con 1.102.057.472 y
1.527.547.135 bytes respectivamente. El usuario autorizó ampliar el máximo
sin recortar funciones ni calidad. El check de tamaño sigue siendo bloqueante.

Los JSON y la ejecución enlazada conservan el límite histórico de 1.500.000.000
bytes: Linux falló únicamente ese control. No se modifican esos resultados
históricos.

### Revalidación con máximo de 2 GB

Commit `ad0891f`, [ejecución 38791061811](https://github.com/GuilleBouix/Yagua-Image-Processor/actions/runs/38791061811):
**Windows y Linux completaron todos los checks correctamente**, sin publicar releases.
En ambos pasaron Ruff, Pyright, 313 tests con Tk obligatorio y las construcciones
comparativas, imports, navegación, OCR/fondo online y offline, igualdad de píxeles
y backend Numba. Total instalado: **1.102.057.456 bytes en Windows** y
**1.527.547.175 bytes en Linux**, ambos por debajo de 2.000.000.000.
El AppImage comprimido conserva sus 341.374.144 bytes. La pequeña variación de
los totales frente a la medición anterior corresponde a las cachés generadas;
no se modificó la lógica de la app, los modelos ni la calidad.

| Comprobación | Windows | Linux |
|---|---|---|
| Instalación limpia y pip check | Pasa | Pasa |
| Ruff / Pyright | Pasa / pasa | Pasa / pasa |
| Suite con Tk obligatorio | 310 tests pasan | 310 tests pasan |
| Build y carga nativa del paquete | Pasa | Pasa |
| Arranque y navegación por los 11 módulos | Pasa | Pasa |
| OCR español, inglés y ambos: online/offline | Pasa | Pasa |
| ISNet y U2NetP: online/offline | Pasa | Pasa |
| Modelos conservan sus SHA256 | Pasa | Pasa |
| Píxeles de nueve conversiones iguales a la base | Pasa | Pasa |
| Píxeles de ambos modelos de fondo iguales a la base | Pasa | Pasa |
| ICC RGB JPEG/WebP retenido en candidato | Pasa | Pasa |
| Límite histórico de 1.500 MB en esa ejecución | Pasa | Falla |

No hubo un fallo de compilación en esa ejecución. El bloqueo de Linux correspondía al límite anterior.
Los modelos ocupan lo mismo antes y después; no se redujeron formatos ni parámetros de calidad.

### Dependencias y recursos retirados por sistema

| Sistema | Retirado del runtime o paquete | Conservado por necesidad |
|---|---|---|
| Ambos | 44 entradas sin uso; herramientas de test/build separadas; pandas, tkinterdnd2 y rembg CLI; datos OCR ajenos a es/en; recursos de instalador/macOS en el ejecutable | Todos los módulos y formatos, modelos, fuentes, licencias y metadatos |
| Windows | OpenCV GUI, plugin FFmpeg de video y protoc de desarrollo | OpenCV headless, TBB/tcmlib, DLL de imagen y bibliotecas numéricas |
| Linux | OpenCV GUI/Qt, TBB de pip que la base tampoco enlazaba al ejecutar; ejecutables de pruebas C++/protoc de Torch; raíces GTK/OpenGL/NSS/GLib/SM/ICE/xkbcommon | OpenCV y su FFmpeg/OpenBLAS enlazado, X11/Xext/Xrender, fuentes y OpenMP |

### Bibliotecas necesarias que mantienen a Linux por encima del objetivo inicial

Los wheels fijados siguen incluyendo estas bibliotecas necesarias:

| Familia | Bytes en el candidato Linux | Uso |
|---|---:|---|
| torch | 522.670.812 | OCR; libtorch_cpu.so concentra 446.534.944 bytes |
| llvmlite | 167.766.616 | Compilación de los kernels de Numba/PyMatting |
| OpenCV | 153.499.857 | Preprocesamiento y sus dependencias nativas enlazadas |
| scipy | 79.925.185 | Procesamiento y refinado de bordes |
| numpy | 42.536.549 | Arrays y operaciones numéricas |
| onnxruntime | 23.587.592 | Inferencia local de quitar fondo |
| Cinco modelos | 296.925.337 | CRAFT, inglés, latino, ISNet y U2NetP |

También permanecen Python/Tk, Pillow, HEIC/AVIF, scikit-image, Torchvision y el código de los módulos.
Los tres OpenBLAS de OpenCV, NumPy y SciPy no se intercambian: los consumidores y ABI difieren.
El hook de Torch ya excluye headers y archivos de desarrollo; se preservan sus módulos y bibliotecas.
Con estos wheels y las restricciones acordadas no se alcanzó el objetivo Linux. No se recortaron SO/DLL ni se usó strip para forzarlo.

### Velocidad y memoria

Cada par se ejecutó secuencialmente en el mismo runner, con las mismas muestras.
Arranque: mediana de tres procesos. Modelos: una pasada offline después de la descarga, en proceso nuevo.
Los datos no acreditan una mejora general de velocidad; los valores individuales dependen del ruido del runner.
En esta pasada Windows tardó más en OCR español (1,721 a 2,164 s) y en procesar
ISNet (2,196 a 2,790 s). Hace falta repetir el benchmark para distinguir una
regresión de la variación del equipo; no se certifica una mejora de rendimiento.

| Sistema | Medición | Antes | Ahora |
|---|---|---:|---:|
| Windows | Arranque, segundos | 1.218 | 1.299 |
| Windows | Carga OCR es, segundos | 2.188 | 2.332 |
| Windows | Carga OCR en, segundos | 1.827 | 1.861 |
| Windows | Carga OCR es+en, segundos | 1.750 | 1.716 |
| Windows | Procesar OCR es, segundos | 1.721 | 2.164 |
| Windows | Procesar OCR en, segundos | 1.608 | 1.586 |
| Windows | Procesar OCR es+en, segundos | 1.689 | 1.689 |
| Windows | Carga ISNet, segundos | 49.895 | 53.060 |
| Windows | Procesar ISNet, segundos | 2.196 | 2.790 |
| Windows | Carga U2NetP, segundos | 0.088 | 0.087 |
| Windows | Procesar U2NetP, segundos | 0.421 | 0.463 |
| Windows | Pico RAM arranque, bytes | 88.629.248 | 86.990.848 |
| Windows | Pico RAM todos los modos, bytes | 3.065.671.680 | 3.045.236.736 |
| Windows | Backend Numba | tbb | tbb |
| Linux | Arranque, segundos | 0.816 | 0.766 |
| Linux | Carga OCR es, segundos | 1.854 | 1.828 |
| Linux | Carga OCR en, segundos | 1.467 | 1.407 |
| Linux | Carga OCR es+en, segundos | 1.505 | 1.440 |
| Linux | Procesar OCR es, segundos | 1.576 | 1.545 |
| Linux | Procesar OCR en, segundos | 1.564 | 1.491 |
| Linux | Procesar OCR es+en, segundos | 1.532 | 1.468 |
| Linux | Carga ISNet, segundos | 40.331 | 38.901 |
| Linux | Procesar ISNet, segundos | 2.028 | 2.058 |
| Linux | Carga U2NetP, segundos | 0.043 | 0.049 |
| Linux | Procesar U2NetP, segundos | 0.359 | 0.349 |
| Linux | Pico RAM arranque, bytes | 92.651.520 | 90.910.720 |
| Linux | Pico RAM todos los modos, bytes | 2.690.039.808 | 2.590.994.432 |
| Linux | Backend Numba | omp | omp |

El pico de RAM es acumulado por proceso. La prueba completa mantiene tres lectores OCR y dos sesiones de fondo;
ese pico no representa la app recién abierta ni el consumo de un único modo.

No se publicó ningún release ni se creó un tag. `main`, el entorno del editor y el borrador de Metadatos quedan intactos.
Se probaron Windows-latest x64 y Ubuntu 22.04/Xvfb. La instalación en equipos limpios sigue siendo manual.

## Matriz de comprobación

| Escenario | Comprobación |
|---|---|
| Dependencias directas e indirectas | Instalación limpia y `pip check`; versiones registradas por plataforma |
| No contaminar el editor | Entornos separados de tests/build; rechazo de paquetes de test/GUI OpenCV en el constructor |
| Imports dinámicos y recursos | Inventario PYZ + navegación por todos los módulos del ejecutable |
| Formatos actuales | Guardado/relectura de JPEG, PNG, WebP, AVIF, HEIC, ICO, BMP, TIFF y GIF |
| Calidad conservada | Comparación de dimensiones, modo y SHA256 de píxeles decodificados con la base, para las nueve conversiones de la muestra |
| Transparencia | Canal alfa comprobado en PNG, WebP, AVIF, HEIC, ICO y TIFF |
| Orientación | EXIF 6 aplicado realmente a las dimensiones de salida |
| Color | ICC RGB retenido en JPEG/WebP; ICC y píxeles intactos al editar metadatos JPEG/TIFF |
| Metadatos | Autor escrito y etiqueta de cámara no editada conservada mediante relectura |
| OCR | Descarga y procesamiento reales de español, inglés y ambos, online y después sin red |
| Quitar fondo | Inferencia real con ISNet y fallback U2NetP forzado, online y después sin red |
| Reutilización de modelos | Cinco pesos presentes, mismos tamaños y SHA256 después de bloquear la red |
| GUI | Tk obligatorio, pantalla inicial, todos los módulos, portapapeles y TXT en un perfil descartable |
| OpenCV sin plugin de video | Imports, decodificación de los nueve formatos y OCR real en el paquete reducido |
| Bibliotecas nativas Linux | Grafo ELF antes de retirar raíces; imports y flujos reales después; no se hace `strip` |
| Límite de tamaño | App + cinco modelos + cachés; test del rechazo justo en el límite y aceptación un byte por debajo |

La muestra sintética permite comparar la misma entrada en ambos paquetes;
no certifica todos los perfiles ICC, cámaras, archivos ni hardware existentes.
La normalización previa de imágenes CMYK/grises a RGB sin gestión de color
permanece como límite, documentado en [bugs.md](bugs.md).

## Pruebas manuales pendientes

1. Abrir el paquete completo con usuario normal y sin Python, desde una ruta con espacios y acentos.
2. Procesar fotografías propias de prueba, revisar colores/transparencias y repetir OCR/quitar fondo sin red tras descargar sus modelos.
3. Windows: instalar/desinstalar con el instalador final. Linux: probar el AppImage en un escritorio limpio, con FUSE y con extracción. CI cubre Windows Server y Ubuntu 22.04/Xvfb; no equivale a certificar Windows 10/11 ni todas las distribuciones/escritorios.
