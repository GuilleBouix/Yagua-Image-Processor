<div align="center">

[English](../../README.md) · **Español** · [Português](README_pt.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · [Italiano](README_it.md) · [日本語](README_ja.md) · [简体中文](README_zh_cn.md) · [Русский](README_ru.md)

<img src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" width="1000" alt="Banner de Yagua — Procesador de imágenes" />

# Yagua · Image Processor

### Tus imágenes. Tu computadora. Tu forma de trabajar.

Herramientas de escritorio gratuitas y de código abierto para convertir, comprimir y procesar imágenes en lote.

**Web oficial**

[Inicio](https://yagua.bouixdev.workers.dev/es/) · [Descargas](https://yagua.bouixdev.workers.dev/es/descargas/) · [Documentación](https://yagua.bouixdev.workers.dev/es/documentacion/) · [Preguntas frecuentes](https://yagua.bouixdev.workers.dev/es/preguntas-frecuentes/)

<p align="center">
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases/latest"><img src="https://img.shields.io/github/v/release/GuilleBouix/Yagua-Image-Processor?style=flat-square&amp;label=stable&amp;color=2563eb" alt="Última versión estable" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases"><img src="https://img.shields.io/github/downloads/GuilleBouix/Yagua-Image-Processor/total?style=flat-square&amp;label=downloads&amp;color=22c55e" alt="Descargas totales" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/GuilleBouix/Yagua-Image-Processor/ci.yml?branch=main&amp;style=flat-square&amp;label=CI" alt="Estado de CI" /></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Python-3.13-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.13" /></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-f4c430?style=flat-square" alt="Licencia MIT" /></a>
</p>

</div>

## Contenido

- [Descargas](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)
- [Funciones](#features)
- [Capturas](#screenshots)
- [Instalación](#installation)
- [Uso](#usage)
- [Requisitos](#requirements)
- [Preguntas frecuentes](#faq)
- [Contribuir](#contributing)

## ¿Por qué Yagua?

Yagua reúne tareas habituales de procesamiento de imágenes en una app de escritorio para desarrolladores web, diseñadores, fotógrafos y cualquiera que trabaje con colecciones de imágenes. Podés procesar tus archivos sin suscripción ni navegador.

El procesamiento corre en tu computadora. Quitar fondo y OCR necesitan una descarga inicial de modelos; después pueden funcionar sin conexión si los modelos necesarios están guardados. Las comprobaciones de actualizaciones consultan GitHub; los enlaces de descarga, donaciones y mapas se abren en el navegador.

La interfaz del código actual admite **inglés, español, portugués, francés, alemán, italiano, japonés, chino simplificado y ruso**, con temas oscuros y vistas previas donde corresponde. Los paquetes publicados pueden incluir menos idiomas; la disponibilidad depende de la versión instalada. El idioma de la interfaz no agrega idiomas de reconocimiento OCR.

<a id="features"></a>

## Funciones

La tabla enumera los módulos de escritorio. La disponibilidad y los controles dependen de la versión instalada; revisá sus notas de publicación.

| Módulo | Qué podés hacer | Formatos y salidas | Límite de selección |
| --- | --- | --- | --- |
| Convertir | Cambiar de formato y ajustar calidad cuando el formato lo permite. | Salidas JPEG, PNG, WebP, AVIF, HEIC, ICO, BMP, TIFF y GIF estático. | 100 imágenes |
| Comprimir | Reducir el tamaño del archivo conservando su formato original. | JPEG, PNG, WebP, AVIF, HEIC/HEIF y otros formatos ráster compatibles. | 100 imágenes |
| Redimensionar / Recortar / Lienzo | Cambiar dimensiones, recortar o agregar espacio; usar tamaños predefinidos. | Imágenes ráster habituales, como JPEG, PNG y WebP. | 100 imágenes |
| Quitar fondo | Eliminar fondos localmente con IA. | Salida PNG, WebP o TIFF con transparencia. | 10 imágenes |
| Paleta de colores | Extraer colores, copiar valores HEX/RGB/HSL y exportar una paleta. | Una imagen compatible → colores y paleta PNG. | 1 imagen |
| Marca de agua | Aplicar un logo; ajustar posición, tamaño, opacidad y margen. | Imágenes base compatibles; se recomienda PNG transparente para el logo. | 100 imágenes + 1 logo |
| Renombrar | Previsualizar numeración, fechas y cambios de mayúsculas/minúsculas. | Cambia los nombres en la carpeta original. | 100 archivos |
| OCR | Extraer texto en español y/o inglés con EasyOCR; copiarlo o exportarlo como TXT. | Imágenes ráster compatibles → texto. | 10 imágenes |
| Metadatos EXIF | Consultar, exportar, editar campos o quitar metadatos en lote. | Edición JPEG/TIFF; exportación de metadatos TXT/JSON. | 1 imagen para editar; 100 para limpiar |
| LQIP / Base64 | Generar placeholders de baja calidad o codificar imágenes para la web. | Base64, data URI, HTML y CSS; exportación TXT/JSON. | 1 imagen |

La compatibilidad depende del módulo, los códecs instalados y la plataforma. Que un formato aparezca en la tabla no garantiza que todos los módulos puedan leerlo o escribirlo. Consultá los [requisitos](#requirements).

<a id="screenshots"></a>

## Capturas

Capturas de Yagua con la interfaz en inglés. Hacé clic en cualquier miniatura para verla en tamaño completo. La distribución y los controles pueden variar entre versiones.

<table>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/home.webp"><img src="../../assets/screenshots/home.webp" width="450" alt="Pantalla inicial con todos los módulos" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/convert.webp"><img src="../../assets/screenshots/convert.webp" width="450" alt="Conversión con imágenes seleccionadas y controles de formato de salida" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/compress.webp"><img src="../../assets/screenshots/compress.webp" width="450" alt="Compresión con controles de calidad y guardado" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/resize.webp"><img src="../../assets/screenshots/resize.webp" width="450" alt="Redimensionado con un preajuste para la cabecera de YouTube" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/remove-background.webp"><img src="../../assets/screenshots/remove-background.webp" width="450" alt="Quitar fondo con una imagen seleccionada" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/palette.webp"><img src="../../assets/screenshots/palette.webp" width="450" alt="Paleta extraída con ocho colores y sus valores" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/watermark.webp"><img src="../../assets/screenshots/watermark.webp" width="450" alt="Controles de marca de agua y vista previa del resultado" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/rename.webp"><img src="../../assets/screenshots/rename.webp" width="450" alt="Renombrado en lote con nombres originales y propuestos" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/ocr.webp"><img src="../../assets/screenshots/ocr.webp" width="450" alt="OCR en inglés con el texto reconocido" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/metadata.webp"><img src="../../assets/screenshots/metadata.webp" width="450" alt="Visor EXIF con selección de imagen, vista previa y campos de metadatos" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/lqip-base64.webp"><img src="../../assets/screenshots/lqip-base64.webp" width="450" alt="Comparación LQIP con la imagen original y data URI generado" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/settings.webp"><img src="../../assets/screenshots/settings.webp" width="450" alt="Ajustes generales con idioma, tema, escala y módulos visibles" /></a></td>
  </tr>
</table>

<a id="installation"></a>

## Instalación

### Elegí una versión

Entrá a **[GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)** y elegí tu sistema operativo. El badge **stable** lleva a la última versión estable de GitHub; las versiones más nuevas marcadas **Pre-release**, incluidas las `rc`, son de prueba. Windows y Linux pueden tener versiones diferentes.

La versión del código se define en [`app/version.py`](../../app/version.py). Eso no significa que exista un instalador publicado con esa misma versión. Leé las notas de cada publicación y descargá los archivos adjuntos a esa release.

| Plataforma | Paquete | Pasos |
| --- | --- | --- |
| Windows | `Yagua_Setup_<version>.exe` | Ejecutá el instalador y abrí Yagua desde Inicio o el acceso directo del escritorio. |
| Windows portable | `Yagua_Portable_<version>.zip`, cuando esté disponible | Extraé todo el ZIP en una carpeta con permisos de escritura y ejecutá `Yagua.exe`. Mantené juntos los archivos que lo acompañan. |
| Linux x86_64 | `Yagua-<version>-x86_64.AppImage`, cuando esté disponible | Dale permiso de ejecución al archivo descargado y ejecutalo como se indica abajo. |
| macOS | Soporte experimental desde código/compilación | No se promete un paquete estable para macOS. Consultá el [script de compilación](../../scripts/build_macos_app.sh) existente. |

En Linux, reemplazá el nombre de ejemplo por el archivo que descargaste:

~~~bash
chmod +x "Yagua-<version>-x86_64.AppImage"
./"Yagua-<version>-x86_64.AppImage"
~~~

### Ejecutar desde el código

Usá **Python 3.13**, la versión utilizada por CI, y Git. La instalación de dependencias puede ser grande porque incluye bibliotecas de OCR e IA. Linux también necesita Tk y las bibliotecas del sistema indicadas en [requisitos](#requirements).

**Windows · PowerShell**

~~~powershell
git clone https://github.com/GuilleBouix/Yagua-Image-Processor.git
cd Yagua-Image-Processor
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
~~~

**Linux · Bash**

~~~bash
git clone https://github.com/GuilleBouix/Yagua-Image-Processor.git
cd Yagua-Image-Processor
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
~~~

Estos comandos usan las dependencias fijadas por el repositorio. Las comprobaciones de CI en Windows/Linux no establecen compatibilidad con otras versiones de Python ni con macOS.

<a id="usage"></a>

## Uso

1. Abrí Yagua y elegí un módulo en la barra lateral.
2. Cargá las imágenes y configurá las opciones disponibles.
3. Revisá la vista previa cuando el módulo la ofrezca.
4. Procesá las imágenes y elegí una carpeta de salida cuando se solicite; revisá el mensaje final por si hubo errores.

**LQIP / Base64:** Seleccioná una imagen, elegí el modo y los parámetros, generá, compará y copiá o exportá Data URI, HTML, CSS o Base64 puro. Cargar otra imagen restablece el modo LQIP, ancho 20 px, desenfoque 2 y calidades 40/85; cancelar el selector conserva el estado actual. Ambos modos generan JPEG sin transparencia.

**Archivos originales:** Renombrar cambia los nombres en su ubicación actual. Editar EXIF sobrescribe la imagen seleccionada después de pedir confirmación. Trabajá con copias para esas operaciones. Limpiar EXIF en lote guarda en la carpeta elegida. Las otras exportaciones usan el flujo de guardado o carpeta de salida de cada módulo.

### Ejemplos prácticos

- **Preparar imágenes para la web:** Convertí hasta 100 fotos a WebP, elegí la calidad y después ajustá el tamaño si hace falta. Generá los placeholders LQIP por separado para mostrar vistas previas mientras carga tu sitio.
- **Preparar fotos de productos:** Cargá hasta 10 imágenes en Quitar fondo y exportá como PNG o WebP para mantener la transparencia. Si hace falta, agregá un logo PNG transparente con Marca de agua.
- **Extraer texto:** Cargá hasta 10 imágenes nítidas en OCR, elegí español, inglés o ambos y copiá el resultado o exportá un TXT. El idioma de la interfaz no agrega idiomas de reconocimiento OCR. Revisá el texto por posibles errores de reconocimiento.

<a id="requirements"></a>

## Requisitos y límites

### Hardware

Para la app completa, incluyendo **OCR y quitar fondo**:

| Componente | Mínimo provisional | Recomendado |
| --- | --- | --- |
| Procesador | Intel/AMD x86-64 relativamente reciente, **4 núcleos** | CPU moderna de **6–8 núcleos** |
| RAM del equipo | **8 GB**, con pocas aplicaciones abiertas | **16 GB**; **32 GB** para imágenes muy grandes y multitarea |
| Almacenamiento | **4 GB libres**, más espacio para originales y resultados | **SSD con 10 GB libres o más**, aparte de tus imágenes |
| Gráficos | Integrados suficientes; sin GPU dedicada obligatoria | Integrados suficientes |
| Internet | Para descargar inicialmente los modelos y buscar actualizaciones | Uso sin conexión con los modelos necesarios descargados |

**Son estimaciones prácticas para la app completa, no mínimos de hardware validados. Todavía falta probarlos en una PC de gama baja.** No se recomienda un equipo con 4 GB de RAM para el uso completo de OCR y quitar fondo. El consumo depende de la resolución, el tamaño del lote y los modelos; reducí los lotes si tenés pocos recursos.

El paquete probado procesa por **CPU**; no necesitás una NVIDIA ni otra GPU dedicada. Priorizá procesador, RAM y SSD. Quitar fondo usa el proveedor de ejecución por CPU de ONNX Runtime; consultá la [documentación oficial de ONNX Runtime](https://onnxruntime.ai/docs/api/python/api_summary.html).

### Sistemas operativos

| Sistema | Base y validación |
| --- | --- |
| Windows | **Windows 10/11 de 64 bits**; preferentemente Windows 11. ONNX Runtime establece Windows 10 como versión mínima de Windows. Falta validar el instalador y el portable finales en PCs limpias con Windows 10/11. |
| Linux | **Ubuntu 22.04 x86-64**, la base comprobada en CI. Otras distribuciones, versiones y escritorios necesitan validación del AppImage final. |
| macOS | Soporte experimental; no se afirma que exista un paquete nativo validado. |

Los paquetes actuales de Windows y Linux son **x86-64**; no hay una versión nativa validada para ARM. CI usa Windows Server y Ubuntu 22.04/Xvfb; esas pruebas no certifican todos los sistemas de escritorio. Consultá los [requisitos de plataforma de ONNX Runtime](https://onnxruntime.ai/docs/build/inferencing.html).

<details>
<summary>Consumo medido y primera carga del modelo</summary>

La auditoría de paquetes registra estas observaciones aproximadas en compilaciones de CI probadas el 15 de octubre de 2026:

| Medición | Windows | Linux |
| --- | --- | --- |
| Pico de RAM del proceso observado con varios modelos cargados | **3,0 GB** | **2,6 GB** |
| App + todos los modelos y cachés medidos en esa prueba | **1,10 GB** | **1,53 GB** |
| Primera carga del modelo para quitar fondo (ISNet) | **53 segundos** | **39 segundos** |

**Son observaciones, no máximos ni tiempos garantizados.** La prueba de RAM mantuvo varios modelos cargados; las fotografías grandes pueden consumir más memoria. Las cifras de disco cubren el paquete, los modelos y las cachés medidos, no originales, resultados, espacio temporal de extracción ni un entorno de desarrollo desde código. Los tiempos de carga dependen del equipo; después se reutiliza la sesión. No son tiempos de descarga del modelo ni de procesamiento por imagen.

</details>

### Ejecución y procesamiento

- **Desde código:** Python 3.13, Tk y las bibliotecas de [`requirements.txt`](../../requirements.txt). Los paquetes compilados no requieren instalar Python por separado.
- **Lotes:** La tabla de funciones muestra los límites actuales de la interfaz: una imagen para Paleta, LQIP / Base64 o edición EXIF, 10 para OCR/quitar fondo y 100 para las otras operaciones en lote indicadas.
- **Códecs:** HEIC/HEIF usa `pillow-heif`, incluido en las dependencias del código. AVIF y otros formatos dependen de los códecs de Pillow y la plataforma. JPEG no admite transparencia; usá PNG o WebP si la necesitás. La compresión PNG puede reducir la imagen a 256 colores: revisá el resultado.
- **Modelos de IA:** Puede haber descargas en el primer uso o al elegir un modelo/idioma que necesite otro modelo. Para trabajar sin conexión deben estar guardados. El paquete probado ejecuta OCR y quitar fondo por CPU.

### Bibliotecas del sistema en Linux

AppImage necesita **FUSE 2** para ejecutarse mediante montaje (`libfuse2` en distribuciones compatibles). Si FUSE no está disponible, podés usar extracción; consultá las [instrucciones oficiales de AppImage](https://docs.appimage.org/user-guide/troubleshooting/fuse.html). Reemplazá el nombre de ejemplo por el archivo descargado:

~~~bash
./"Yagua-<version>-x86_64.AppImage" --appimage-extract-and-run
~~~

La extracción necesita espacio temporal adicional y puede demorar el inicio. Para ejecutar desde código, CI instala Tk y estas bibliotecas en Ubuntu 22.04:

~~~bash
sudo apt-get install python3-tk libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgtk-3-0 libgomp1
~~~

Los nombres de los paquetes varían según la distribución. Verificá que Tk esté disponible para tu intérprete Python 3.13; el paquete Tk predeterminado de la distribución puede no cubrir un Python instalado por separado.

<a id="faq"></a>

## Preguntas frecuentes

### ¿Yagua sube mis imágenes?

El procesamiento es local; los módulos no suben imágenes a un servicio de procesamiento. Descargar modelos y comprobar actualizaciones en GitHub requiere conexión. Los enlaces externos abren el navegador; al abrir el enlace de mapa de EXIF, las coordenadas GPS seleccionadas se envían a Google Maps.

### ¿Por qué tarda más la primera operación con IA?

OCR y Quitar fondo inicializan sus motores y pueden descargar modelos. Esperá a que termine ese paso. Las siguientes ejecuciones pueden reutilizar los modelos guardados; las imágenes y los lotes grandes siguen necesitando más recursos.

### ¿Por qué no está disponible un formato o se rechaza una imagen?

Las entradas admitidas dependen del módulo y los códecs disponibles. Probá con una copia PNG o JPEG y revisá `yagua.log`. Exportá como PNG o WebP si necesitás transparencia.

### ¿Por qué la compresión no reduce todas las imágenes?

Una imagen ya optimizada puede no reducirse. Si quitar EXIF está desactivado, Yagua copia el original a la salida cuando la compresión produciría un archivo igual o más grande. Si quitar EXIF está activado, guarda la imagen procesada aunque pese más, para que ese reemplazo por el original no restaure sus EXIF. Para un flujo específico de limpieza EXIF, usá el módulo de metadatos.

### ¿Cómo funcionan las actualizaciones?

Yagua puede avisarte al iniciar y permite comprobar desde **Ajustes → Actualizaciones**. Abre un enlace de descarga; no instala actualizaciones automáticamente. Los paquetes RC.4/RC.5 solo buscan versiones estables más nuevas con el prefijo de tu plataforma (`win-v` o `linux-v`); excluyen preliminares y borradores, así que no detectan nuevas RC. Descargá las versiones de prueba manualmente desde [GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases). Esos paquetes también pueden indicar «No hay actualizaciones» tras un fallo de conexión; si tenés dudas, revisá Releases directamente, incluidas las publicaciones antiguas sin prefijo de plataforma.

### ¿Cómo reporto un problema?

Abrí un [reporte de error](https://github.com/GuilleBouix/Yagua-Image-Processor/issues/new?template=bug_report.md) con tu versión de Yagua, sistema operativo, módulo, pasos para reproducirlo y logs relevantes. Buscá `yagua.log` en:

- Windows: `%APPDATA%\Yagua\yagua.log`
- Linux: `~/.config/Yagua/yagua.log`
- macOS: `~/Library/Application Support/Yagua/yagua.log`

Los logs pueden incluir rutas y nombres de archivos; revisalos antes de compartirlos.

<a id="contributing"></a>

## Desarrollo y contribución

Yagua usa **CustomTkinter** para la interfaz, **Pillow / pillow-heif** para imágenes, **rembg / ONNX Runtime** para quitar fondos, **EasyOCR / PyTorch** para OCR y **piexif** para EXIF. Las versiones exactas están en [`requirements.txt`](../../requirements.txt).

Después de instalar desde código, instalá las herramientas de desarrollo y ejecutá las comprobaciones de CI. En Windows, usá directamente los ejecutables del entorno virtual:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m pyright --skipunannotated --pythonpath .\.venv\Scripts\python.exe app
.\.venv\Scripts\python.exe -m pytest -q
~~~

En Linux, con el entorno virtual activado:

~~~bash
python -m pip install -r requirements-dev.txt
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m pytest -q
~~~

Los tests de interfaz necesitan una pantalla. En Linux sin entorno gráfico, instalá `xvfb` y usá `xvfb-run -a python -m pytest -q`, como hace CI.

Consultá [`CHANGELOG.md`](../../CHANGELOG.md) para el historial. Algunas capturas pueden estar atrasadas respecto del código. Reportá errores, proponé funciones en [Issues](https://github.com/GuilleBouix/Yagua-Image-Processor/issues) o enviá PR con cambios concretos y validación relevante. Si cambiás comportamientos documentados, actualizá los nueve idiomas del README.

## Apoyá el proyecto

Si Yagua te sirve, una estrella en GitHub ayuda a que otros lo encuentren. También podés colaborar con reportes, traducciones o contribuciones.

**[¿Ya probaste Yagua? Dejá tu valoración](https://yagua.bouixdev.workers.dev/es/proyecto/#project-rating)**

**[Apoyar en GitHub Sponsors](https://github.com/sponsors/GuilleBouix) · [Apoyar por PayPal](https://www.paypal.com/paypalme/guillebouix)**

<p align="center">
  <a href="https://www.paypal.com/paypalme/guillebouix"><img src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" width="220" alt="Apoyá a Yagua por PayPal" /></a>
</p>

## Licencia

Yagua se distribuye bajo la **[licencia MIT](../../LICENSE)**. Las bibliotecas y los modelos de terceros conservan sus respectivas licencias.
