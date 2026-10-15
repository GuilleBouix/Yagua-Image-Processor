# Runtime reducido — Yagua

Rama: `codex/lean-runtime`. Base de comparación: `1914a11`.

## Política

- `requirements.txt`: ejecución, 51 dependencias fijadas; un solo OpenCV, headless 4.13.0.92.
- `requirements-dev.txt`: pytest, cobertura, Ruff y Pyright. Entorno separado.
- `requirements-build.txt`: PyInstaller y sus herramientas. Entorno separado del de tests y del editor.
- Linux conserva Torch/Torchvision CPU explícitos. No se cambian motores, modelos, parámetros de calidad ni formatos.
- Se retiran 45 entradas ajenas a la ejecución, seis pasan a desarrollo y cinco a construcción. Lista exacta: [dependencies.json](dependencies.json).
- Se conservan Torch, Torchvision, ONNX Runtime, NumPy, SciPy, Numba, llvmlite y PyMatting. No se recortan sus módulos internos ni DLL/SO arbitrarias.
- Los imports estáticos resuelven la API y las sesiones de rembg. Se excluyen sus comandos/CLI; se conserva su registro de sesiones completo, porque el paquete lo importa al inicializar.
- Torch conserva todos sus módulos y bibliotecas. Se excluyen exclusivamente sus ejecutables de pruebas C++ y el compilador Protobuf; permanece `torch_shm_manager`.
- EasyOCR conserva código/configuración compartidos, CRAFT, reconocimiento inglés y latino. Solo se empaquetan recursos de idiomas español/inglés: son las opciones actuales de OCR, independientemente del idioma de la interfaz.
- Recursos del instalador y macOS quedan en el repositorio. Fuentes, iconos de la app, licencias, metadatos y codecs permanecen en el paquete.
- La DLL `opencv_videoio_ffmpeg*` es exclusivamente de video. Su exclusión se comprueba con imports nativos, los nueve formatos y OCR real en el ejecutable.
- Linux: la inspección de dependencias ELF encontró cero consumidores de GTK, OpenGL y Mozilla NSS en el paquete de la app ni en su cierre de dependencias. Se retiran esas tres raíces de la receta; la evidencia previa está en [linux-native-before.json](linux-native-before.json). Se conservan X11, fuentes, OpenMP y las dependencias de Tk. FFmpeg y OpenBLAS de OpenCV en Linux sí están enlazados y permanecen.

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

En cada plataforma:

1. Entorno de tests nuevo: instalación y `pip check`, Ruff, Pyright y suite completa, con Tk obligatorio.
2. Construcción de la base y del candidato, secuencialmente en el mismo runner y con entornos nuevos. El único cambio sobre la base es el mismo verificador optativo que usa el candidato; su lógica, requisitos y especificación originales se conservan.
3. Linux construye AppImage y verifica su runtime y la extracción. Windows construye la carpeta portable y ZIP.
4. Tres arranques con dibujo de la pantalla inicial, sin red. Se registra tiempo total del proceso, incluido arranque y cierre.
5. Pruebas online con descarga, luego en un proceso nuevo con sockets bloqueados: español, inglés, ambos; modelos principal y fallback; transparencia, nueve formatos, orientación, píxeles/ICC/EXIF; navegación de todos los módulos, portapapeles y exportación TXT. Los SHA256 de los modelos deben conservarse y las nueve conversiones deben decodificar a los mismos píxeles que la base.
6. Se registran carga de modelos, procesamiento, tiempo y pico de memoria residente del proceso por etapa. Es un pico acumulado, no memoria exclusiva de esa etapa. La descarga online depende de la red; comparar las etapas offline para tiempos de carga/procesamiento.
7. Inventario congelado: módulos prohibidos, recursos OCR, DLL de video y recursos ajenos a la plataforma.

Los procesos de verificación reciben un perfil de usuario, carpetas de fuentes,
preferencias y temporales propios antes de importar Tk; también se incluyen esas
cachés en la medición. No se modifica el perfil real del editor.

Desde el repositorio, con Python 3.13:

```powershell
python scripts/ci/validate_lean_runtime.py --reports lean-reports
```

Linux requiere las dependencias nativas listadas en el workflow y ejecuta las pruebas gráficas con Xvfb. Los entornos temporales de cada construcción se liberan al terminar; los informes quedan en la carpeta indicada.

## Medición y límite

Límite estricto: **1.500.000.000 bytes**. Se suma el tamaño lógico de archivos regulares de:

- App portable descomprimida en Windows / AppImage extraído completo en Linux.
- Los cinco modelos y recursos que descargan sus bibliotecas.
- Cachés persistentes de ejecución y perfil generado por las pruebas.

El ZIP/AppImage comprimido se informa aparte. No se cuentan los entornos de desarrollo/construcción, imágenes temporales usadas en pruebas ni informes. No se suman componentes solapados ni se cuentan dos veces los enlaces simbólicos internos.

`scripts/ci/check_installed_size.py` rechaza el total fuera del límite y enumera los archivos más pesados. Los workflows de release aplican este control después de los tests online/offline y antes de publicar. Un control preliminar del paquete por sí solo no certifica el total instalado.

## Resultados

Las mediciones finales y los resultados por plataforma se incorporarán tras completar las construcciones comparativas. Hasta entonces, el objetivo de tamaño y la compatibilidad del paquete reducido no se consideran aprobados.

Las pruebas automáticas no sustituyen probar el instalador/AppImage en equipos limpios ni garantizan velocidad idéntica en otro hardware. No se publica ningún release como parte de este trabajo.
