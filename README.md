<img width="1761" height="497" alt="banner" src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" />

# Yagua - Image Processor

---

## 🇬🇧 English

### Table of Contents

- [Description](#-description)
- [Features](#-features)
- [Gallery](#️-gallery)
- [Installation](#️-installation)
- [Requirements](#-recommended-requirements)
- [Usage](#-usage)
- [Technologies](#-technologies-used)
- [Contributing](#-contributing)
- [Support the project](#-support-the-project)
- [License](#-license)

---

### 📖 Description

Yagua was born as an alternative to web-based image processing tools: limited and paywalled for tasks that should be simple. It's a free, open source desktop app that runs everything locally.

Built for web developers, designers, photographers, and anyone who needs to process images in bulk without relying on a browser or paying a subscription.

Yagua brings together in a single interface features oriented toward modern web workflows: LQIP and Base64 generation, AI background removal (rembg, works offline once the model is downloaded), EXIF metadata editing, and batch compression/conversion with practical per-module limits.

### ✨ Features

- Smart compression with quality control
- Conversion between multiple image formats
- AI background removal (rembg)
- Resize, crop and canvas editing
- Image transformation (rotation, flip, EXIF)
- Automatic color palette extraction
- Bulk renaming with live preview
- Watermark with real-time preview
- OCR (EasyOCR)
- Vectorization to SVG (vtracer)
- EXIF metadata management (view, edit and clean)
- LQIP generation and Base64 encoding
- HEIC/HEIF support (requires `pillow-heif`)
- Multi-language support (ES / EN / PT / FR / DE)
- New version notification on startup + link to download the latest release
- Settings with tabs (Settings / Updates)
- Welcome screen on app launch
- Detailed per-module logs for diagnostics
- Predefined dark themes

### 🖼️ Gallery

<p align="center">
  <img src="https://github.com/user-attachments/assets/f8f57bbb-4cdf-4c5f-8d06-a04b2c3dc1b1" width="250" alt="1"/>
  <img src="https://github.com/user-attachments/assets/903c897e-eb48-4b6b-b941-2fbfffb234ce" width="250" alt="2"/>
  <img src="https://github.com/user-attachments/assets/ed7081e4-d106-47db-9744-927be0db9d5d" width="250" alt="3"/>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/381c1f71-debd-47a0-837b-fb8f84e41790" width="250" alt="4"/>
  <img src="https://github.com/user-attachments/assets/dfe2dd77-f792-4092-a6d7-82b5e96aa104" width="250" alt="5"/>
  <img src="https://github.com/user-attachments/assets/e3a8f766-84e5-412d-bbaf-acb5936c0380" width="250" alt="6"/>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/235fce12-9796-4304-9252-f9e016edf483" width="250" alt="7"/>
  <img src="https://github.com/user-attachments/assets/8e8824a4-0bdf-44d8-b82f-7e0c2e1fcfe5" width="250" alt="8"/>
  <img src="https://github.com/user-attachments/assets/29131d50-2ea2-40c5-9549-d5878d89119a" width="250" alt="9"/>
</p>

### ⚙️ Installation

#### 🖥️ Installation (Windows)

1. Download `Yagua_Setup_2.X.X.exe`
2. Run the installer
3. Follow the installation instructions
4. Launch the app from the desktop or Start menu

#### 🐧 Installation (Linux)

1. Download `Yagua-2.X.X-x86_64.AppImage`
2. Run in terminal: `chmod +x Yagua-2.X.X-x86_64.AppImage`
3. Then: `./Yagua-2.X.X-x86_64.AppImage`

#### 🐍 Source code

1. Clone the repository.
2. Create and activate your virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Run `python main.py`.

### 🧩 Recommended Requirements

For Yagua to run smoothly, especially with large batches (up to 100 images):

#### ✅ System

- Windows 10/11 or Linux x64
- CPU: 4 cores or more recommended
- RAM: 6 GB minimum
- Disk: 500 MB free + space for outputs

#### ✅ Dependencies (Linux)

- AppImage usually runs out of the box, but may require:
  - `libfuse2`
  - `libgl1`
  - `libglib2.0-0`

#### ✅ Batch Limits

- 100 images per batch (compression, conversion, resize, rename, LQIP)
- 10 images per batch for Background Removal
- 10 images per batch for OCR
- 50 images per batch for Vectorize (also skips files over 1 MB) — accepts `PNG/WEBP/TIFF/HEIC/HEIF`
- 100 images per batch for Transform and Watermark
- 100 images for metadata cleanup (EXIF)

### 🚀 Usage

1. Open the app.
2. Select a module from the sidebar.
3. Load images and process.
4. Save results to the output folder.

Updates:

- If a newer version is available, Yagua shows a notice inside the app on startup.
- You can also go to `Settings → Updates` and open the download link.

ℹ️ Note: macOS is in experimental phase.

### 🔧 Technologies Used

| Technology    | Version | Purpose                      |
| ------------- | ------- | ---------------------------- |
| Python        | 3.13+   | Main language                |
| CustomTkinter | 5.2.2   | Modern desktop UI            |
| Pillow        | 12.1.1  | Image processing             |
| pillow-heif   | 1.x     | HEIC/HEIF support for Pillow |
| piexif        | 1.1.3   | EXIF metadata                |
| rembg         | 2.0.73  | AI background removal        |
| EasyOCR       | 1.x     | Local OCR (CPU/GPU)          |
| vtracer       | 0.x     | Raster → SVG vectorization   |
| Codex         | N/A     | Development assistance       |

### 🤝 Contributing

- Open an issue for bugs or ideas.
- Submit a PR with clear, small changes.
- Keep the project's style and current structure.

### ⭐ Support the Project

If Yagua was useful to you, leave a star on the repo — it's free and helps a lot for more people to find it :)

<a href="https://www.paypal.com/paypalme/guillebouix?locale.x=es_XC&country.x=AR" target="_blank"><img width="300" alt="paypal_donate_button" src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" />
</a>

### 📄 License

MIT License - See LICENSE file for more details.

---

&nbsp;

---

---

---

&nbsp;

---

## 🇦🇷 Español

### Índice

- [Descripción](#-descripción)
- [Features](#-features-1)
- [Galería](#️-galería)
- [Instalación](#️-instalación)
- [Requisitos](#-requisitos-recomendados)
- [Uso](#-uso)
- [Tecnologías](#-tecnologías-utilizadas)
- [Contribución](#-contribución)
- [Apoyá el proyecto](#-apoyá-el-proyecto)
- [Licencia](#-licencia)

---

### 📖 Descripción

Yagua surgió como alternativa a las herramientas web de procesamiento de imágenes: limitadas y con planes de pago para tareas que deberían ser simples. Es una app de escritorio gratuita y open source que corre todo localmente.

Está pensada para desarrolladores web, diseñadores, fotógrafos y cualquier usuario que necesite procesar imágenes en lote sin depender de un navegador ni pagar una suscripción.

Yagua integra en una sola interfaz features orientadas al flujo de trabajo web moderno: generación de LQIP y Base64, quitar fondo con IA (rembg, funciona offline una vez descargado el modelo), edición de metadatos EXIF y compresión/conversión en lote con límites prácticos por módulo.

### ✨ Features

- Compresión inteligente con control de calidad
- Conversión entre múltiples formatos de imagen
- Eliminación de fondo con IA (rembg)
- Redimensionado, recorte y edición en canvas
- Transformación de imágenes (rotación, flip, EXIF)
- Extracción automática de paleta de colores
- Renombrado masivo con vista previa
- Marca de agua con preview en tiempo real
- OCR (EasyOCR)
- Vectorización a SVG (vtracer)
- Gestión de metadatos EXIF (visualizar, editar y limpiar)
- Generación de LQIP y codificación Base64
- Soporte HEIC/HEIF (requiere `pillow-heif`)
- Soporte multi-idioma (ES / EN / PT / FR / DE)
- Aviso de nuevas versiones al iniciar + enlace para descargar la última release
- Ajustes con tabs (Ajustes / Actualizaciones)
- Pantalla de bienvenida al abrir la app
- Logs detallados por módulo para diagnóstico
- Temas oscuros predefinidos

### 🖼️ Galería

<p align="center">
  <img src="https://github.com/user-attachments/assets/f8f57bbb-4cdf-4c5f-8d06-a04b2c3dc1b1" width="250" alt="1"/>
  <img src="https://github.com/user-attachments/assets/903c897e-eb48-4b6b-b941-2fbfffb234ce" width="250" alt="2"/>
  <img src="https://github.com/user-attachments/assets/ed7081e4-d106-47db-9744-927be0db9d5d" width="250" alt="3"/>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/381c1f71-debd-47a0-837b-fb8f84e41790" width="250" alt="4"/>
  <img src="https://github.com/user-attachments/assets/dfe2dd77-f792-4092-a6d7-82b5e96aa104" width="250" alt="5"/>
  <img src="https://github.com/user-attachments/assets/e3a8f766-84e5-412d-bbaf-acb5936c0380" width="250" alt="6"/>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/235fce12-9796-4304-9252-f9e016edf483" width="250" alt="7"/>
  <img src="https://github.com/user-attachments/assets/8e8824a4-0bdf-44d8-b82f-7e0c2e1fcfe5" width="250" alt="8"/>
  <img src="https://github.com/user-attachments/assets/29131d50-2ea2-40c5-9549-d5878d89119a" width="250" alt="9"/>
</p>

### ⚙️ Instalación

#### 🖥️ Instalación (Windows)

1. Descargar `Yagua_Setup_2.X.X.exe`
2. Ejecutar el instalador
3. Seguir instrucciones de instalación
4. Ejecutar la app desde el escritorio o el menú Inicio

#### 🐧 Instalación (Linux)

1. Descargar `Yagua-2.X.X-x86_64.AppImage`
2. Ejecutar en terminal `chmod +x Yagua-2.X.X-x86_64.AppImage`
3. Luego `./Yagua-2.X.X-x86_64.AppImage`

#### 🐍 Código fuente

1. Clona el repositorio.
2. Crea y activa tu entorno virtual.
3. Instala dependencias con `pip install -r requirements.txt`.
4. Ejecuta `python main.py`.

### 🧩 Requisitos Recomendados

Para que Yagua funcione de manera fluida, especialmente con lotes grandes (hasta 100 imágenes):

#### ✅ Sistema

- Windows 10/11 o Linux x64
- CPU: 4 núcleos o más recomendado
- RAM: 6 GB mínimo
- Disco: 500 MB libres + espacio para outputs

#### ✅ Dependencias (Linux)

- AppImage suele correr directo, pero puede requerir:
  - `libfuse2`
  - `libgl1`
  - `libglib2.0-0`

#### ✅ Límites de carga

- 100 imágenes por lote (compresión, conversión, resize, rename, LQIP)
- 10 imágenes por lote en Quitar Fondo
- 10 imágenes por lote en OCR
- 50 imágenes por lote en Vectorizar (además omite archivos de más de 1 MB) — acepta `PNG/WEBP/TIFF/HEIC/HEIF`
- 100 imágenes por lote en Transformar y Marca de agua
- 100 imágenes en limpieza de metadatos (EXIF)

### 🚀 Uso

1. Abre la app.
2. Selecciona un módulo en la barra lateral.
3. Carga imágenes y procesa.
4. Guarda los resultados en la carpeta de salida.

Actualizaciones:

- Si hay una versión más nueva, Yagua muestra un aviso dentro de la app al iniciar.
- También podés ir a `Ajustes → Actualizaciones` y abrir el enlace de descarga.

ℹ️ Nota: macOS está en fase experimental.

### 🔧 Tecnologías Utilizadas

| Tecnología    | Versión | Propósito                   |
| ------------- | ------- | --------------------------- |
| Python        | 3.13+   | Lenguaje principal          |
| CustomTkinter | 5.2.2   | UI moderna para escritorio  |
| Pillow        | 12.1.1  | Procesamiento de imágenes   |
| pillow-heif   | 1.x     | Soporte HEIC/HEIF en Pillow |
| piexif        | 1.1.3   | Metadatos EXIF              |
| rembg         | 2.0.73  | Quitar fondo con IA         |
| EasyOCR       | 1.x     | OCR local (CPU/GPU)         |
| vtracer       | 0.x     | Vectorización raster → SVG  |
| Codex         | N/A     | Asistencia de desarrollo    |

### 🤝 Contribución

- Abre un issue para bugs o ideas.
- Envía un PR con cambios claros y pequeños.
- Mantén el estilo del proyecto y la estructura actual.

### ⭐ Apoyá el Proyecto

Si Yagua te resultó útil, dejá una estrella en el repo — es gratis y ayuda un montón a que más gente lo encuentre :)

<a href="https://www.paypal.com/paypalme/guillebouix?locale.x=es_XC&country.x=AR" target="_blank"><img width="300" alt="paypal_donate_button" src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" />
</a>

### 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles.
