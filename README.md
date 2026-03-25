<img width="1761" height="497" alt="banner" src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" />

# Yagua - Procesador de Imágenes

Aplicación de escritorio para procesar imágenes en lote con una interfaz moderna, rápida y enfocada en productividad.

---

## Tabla de Contenidos

1. [Descripción](#descripcion)
2. [Características Principales](#caracteristicas-principales)
3. [Galería](#galeria)
4. [Instalación y Uso](#instalacion-y-uso)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Stack Tecnológico](#stack-tecnologico)
7. [Estructura del Proyecto](#estructura-del-proyecto)
8. [Arquitectura](#arquitectura)
9. [Módulos Implementados](#modulos-implementados)
10. [Sistema de Traducciones](#sistema-de-traducciones)
11. [Contribución](#contribucion)
12. [Licencia](#licencia)

---

## Descripción

Yagua es una app de escritorio para procesamiento masivo de imágenes. Incluye compresión, conversión, remoción de fondo con IA, edición EXIF, generación de LQIP/Base64 y más. Está pensada para flujos de trabajo rápidos sin depender de herramientas web o servicios externos.

---

## Características Principales

- **Compresión de imágenes**: reduce tamaño manteniendo buena calidad.
- **Conversión de formatos**: JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF.
- **Extracción de paleta**: colores dominantes en distintos formatos.
- **Gestión de metadatos EXIF**: lectura, edición, limpieza y exportación.
- **Redimensionar / Recortar / Canvas**: presets y tamaños personalizados.
- **Renombrar por lotes**: patrones configurables y preview en tiempo real.
- **Quitar fondo con IA**: usando `rembg`.
- **LQIP / Base64**: placeholders listos para web.
- **Multiidioma**: Español, English, Português.
- **Marca de agua** (roadmap): texto o imagen con opacidad configurable.
- **Optimizer** (roadmap): optimización inteligente automatizada.

---

## Galería

<!-- TODO: agregar capturas de pantalla de la app -->

---

## Instalación y Uso

### Requisitos del Sistema

- Windows 10/11 (macOS y Linux parcialmente soportados)
- Python 3.13 o superior
- 4 GB de RAM recomendada

### Instalación

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install customtkinter==5.2.2 pillow==12.1.1 piexif==1.1.3 tkinterdnd2==0.4.3 rembg==2.0.57
```

### Ejecutar la aplicación

```bash
python -m app.main
```

O usando el entrypoint de compatibilidad:

```bash
python main.py
```

### Tema y colores

La aplicación usa tema oscuro por defecto. Los colores están definidos en `app/ui/colors.py`:

```python
FRAMES_BG = '#0A0A0B'       # Fondo principal
SIDEBAR_BG = '#121214'      # Fondo del sidebar
PANEL_BG = '#1C1C1E'        # Fondo de paneles
TEXT_COLOR = '#F2F2F7'      # Color de texto principal
ACENTO = '#FFFFFF'          # Color de acento
```

### Inicio maximizado

La aplicación se inicia maximizada automáticamente usando `self.state('zoomed')` en Windows.

---

## Ejemplos de Uso

Ejecutar la app:

```bash
python -m app.main
```

Probar un módulo específico desde consola:

```bash
python -c "from app.modules.compress import comprimir_imagen; print(comprimir_imagen('input.jpg', 'output.jpg'))"
```

---

## Stack Tecnológico

| Tecnología        | Versión | Propósito                               |
| ----------------- | ------- | --------------------------------------- |
| **Python**        | 3.13+   | Lenguaje principal                      |
| **CustomTkinter** | 5.2.2   | UI moderna para desktop                 |
| **Pillow**        | 12.1.1  | Procesamiento de imágenes               |
| **piexif**        | 1.1.3   | Manipulación de metadatos EXIF          |
| **tkinterdnd2**   | 0.4.3   | Drag & Drop                             |
| **darkdetect**    | 0.8.0   | Detección de tema del sistema           |
| **rembg**         | 2.0.57  | Remoción de fondo con IA                |
| **Codex**         | N/A     | Asistencia de desarrollo (OpenAI Codex) |

---

## Estructura del Proyecto

```
Yagua/
|-- main.py                   # Punto de entrada de compatibilidad
|-- app/                      # Código de la aplicación
|   |-- main.py               # Punto de entrada principal
|   |-- app.py                # Clase principal YaguaApp
|   |-- user_settings.json    # Configuración del usuario
|   |-- core/                 # Lógica de negocio (re-exports)
|   |-- modules/              # Módulos de procesamiento de imagen
|   |   |-- compress.py        # Compresión de imágenes
|   |   |-- convert.py         # Conversión de formatos
|   |   |-- palette.py         # Extracción de paleta de colores
|   |   |-- metadata.py        # Gestión de metadatos EXIF
|   |   |-- resize.py          # Redimensionado, recorte y canvas
|   |   |-- remove_bg.py       # Quitar fondo con IA
|   |   |-- lqip.py            # LQIP / Base64
|   |   `-- rename.py          # Renombrado por lotes
|   |-- ui/                   # Interfaz de usuario
|   |   |-- main_window.py     # Ventana principal
|   |   |-- sidebar.py         # Barra lateral de navegación
|   |   |-- colors.py          # Paleta de colores
|   |   |-- fonts.py           # Configuración de fuentes
|   |   `-- frames/            # Frames de cada módulo
|   |       |-- base.py
|   |       |-- compress/
|   |       |-- convert/
|   |       |-- palette/
|   |       |-- metadata/
|   |       |-- resize/
|   |       |-- settings/
|   |       |-- rename/
|   |       |-- remove_bg/
|   |       |-- lqip/
|   |       `-- placeholder_frame.py
|   |-- translations/         # Sistema de traducciones
|   |   |-- __init__.py
|   |   |-- es.py
|   |   |-- en.py
|   |   `-- pt.py
|   `-- utils/                # Helpers
|       `-- __init__.py
`-- assets/                   # Recursos estáticos
    |-- icon.ico
    |-- icon.png
    |-- fonts/
    |   `-- Inter.ttf
    `-- icons/
```

---

## Arquitectura

### Patrón de Arquitectura

El proyecto sigue una arquitectura **MVC simplificada** con separación clara de responsabilidades:

- **Presentation Layer (`app/ui/`)**
  - `frames/` → Vistas (`CTkFrame`)
  - `main_window.py` → Controlador principal
  - `sidebar.py` → Navegación
  - `translations/` → Sistema de traducciones

- **Business Logic Layer (`app/modules/`)**
  - `compress.py`, `convert.py`, `palette.py`, `metadata.py`, `resize.py`, etc.

- **Utilities (`app/utils/`)**
  - `tintar_icono()` y helpers comunes

### Flujo de Datos

1. **Usuario** interactúa con la UI (frames)
2. **Frame** invoca funciones de `services.py` del módulo
3. **Services** delega en `app/modules/` para el procesamiento con Pillow
4. **Resultado** retorna al frame y se actualiza la UI

### Clases Principales

| Clase            | Ubicación                   | Responsabilidad                   |
| ---------------- | --------------------------- | --------------------------------- |
| `YaguaApp`       | `app/app.py`                | Ventana principal, inicialización |
| `MainWindow`     | `app/ui/main_window.py`     | Contenedor con sidebar y frames   |
| `Sidebar`        | `app/ui/sidebar.py`         | Navegación entre módulos          |
| `ModuleRegistry` | `app/ui/module_registry.py` | Registro central de módulos       |
| `BaseFrame`      | `app/ui/frames/base.py`     | Clase base con métodos comunes    |
| `SettingsFrame`  | `app/ui/frames/settings/`   | Configuración (idioma, tema)      |

---

## Módulos Implementados

### 1. Compresión (`compress.py`)

**Funcionalidades:**

- Compresión de imágenes con calidad configurable (10-100)
- Eliminación opcional de metadatos EXIF
- Estimación de tamaño antes de comprimir
- Preservación del formato original o conversión automática
- Soporte para JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF
- Vista previa de imágenes cargadas

**Funciones públicas:**

```python
comprimir_imagen(ruta_entrada, ruta_salida, calidad=85, quitar_exif=True) -> dict
estimar_tamano(ruta_entrada, calidad) -> int
formatear_bytes(bytes_val) -> str
```

### 2. Conversión (`convert.py`)

**Funcionalidades:**

- Conversión entre múltiples formatos
- Calidad configurable por formato
- Corrección automática de modos de color (RGBA → RGB para JPEG)
- Soporte para conversión por lotes
- Vista previa de imágenes cargadas

**Formatos soportados:** JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF

**Funciones públicas:**

```python
convertir_imagen(ruta_entrada, fmt_destino, carpeta_salida, calidad=90) -> dict
batch_convertir(rutas, fmt_destino, carpeta_salida, calidad=90, progress_cb=None) -> list
```

### 3. Paleta de Colores (`palette.py`)

**Funcionalidades:**

- Extracción de N colores dominantes (4-12)
- Conversión de colores a múltiples formatos (HEX, RGB, HSL, CSS)
- Exportación de paleta como imagen PNG
- Detección de luminosidad para texto legible
- Copiar color al portapapeles en diferentes formatos

**Funciones públicas:**

```python
extraer_paleta(ruta, n_colores=6) -> list[tuple[int, int, int]]
rgb_a_hex(rgb) -> str
rgb_a_hsl(rgb) -> tuple[int, int, int]
es_color_claro(rgb) -> bool
formatos_color(rgb) -> dict[str, str]
exportar_paleta_imagen(paleta, ruta_salida, ...) -> str
```

### 4. Metadatos EXIF (`metadata.py`)

**Funcionalidades:**

- Lectura de metadatos EXIF
- Edición de campos (Autor, Copyright, Software, Fecha)
- Limpieza de metadatos por lotes
- Exportación a TXT y JSON
- Coordenadas GPS con enlace a Google Maps
- Soporte para JPEG y TIFF

**Funciones públicas:**

```python
leer_metadatos(ruta) -> dict[str, str]
limpiar_exif(ruta_entrada, ruta_salida) -> dict
editar_exif(ruta_entrada, ruta_salida, campos) -> bool
exportar_txt(metadatos, ruta)
exportar_json(metadatos, ruta)
```

### 5. Redimensionar (`resize.py`)

**Funcionalidades:**

- **Redimensionar**: por porcentaje o píxeles, manteniendo relación de aspecto
- **Recortar**: recorte centrado con dimensiones personalizadas
- **Canvas**: ajusta el tamaño del canvas con color de fondo (blanco, negro, transparente)
- **Presets**: Instagram, Facebook, Twitter/X, YouTube, LinkedIn, TikTok, Pinterest, Web, resoluciones estándar e íconos

**Presets disponibles:**

- Instagram: Post cuadrado 1:1, Post portrait 4:5, Story/Reels 9:16
- Facebook: Post 1200×630, Cover 851×315
- Twitter/X: Post 16:9, Header 3:1
- YouTube: Thumbnail 16:9, Channel art 16:9
- LinkedIn: Post 1.91:1, Cover personal 4:1
- TikTok/WhatsApp: Status/Video 9:16
- Pinterest: Pin estándar 2:3
- Web: OG image 1.91:1
- Resoluciones: HD 720p, Full HD 1080p, 2K, 4K UHD
- Íconos: Favicon 32×32, Ícono 256, Ícono 512

### 6. Renombrar Lote (`rename/frame.py`)

**Funcionalidades:**

- Renombrado por prefijo, sufijo o reemplazo de texto
- Numeración secuencial
- Fecha de modificación como parte del nombre
- Preview de los nuevos nombres antes de aplicar

### 7. Quitar Fondo (`remove_bg/frame.py`)

**Funcionalidades:**

- Eliminación de fondo usando IA (rembg)
- Soporte para personas, productos, dibujos, etc.
- Exportación en PNG con transparencia

### 8. LQIP (`lqip/frame.py`)

**Funcionalidades:**

- Genera Low Quality Image Placeholders
- Exporta en Base64
- Vista previa de las miniaturas

### 9. Settings (`settings/frame.py`)

**Funcionalidades:**

- Cambio de idioma (Español, English, Português)
- Reinicio automático de la app al cambiar idioma

### Roadmap

- **Marca de agua**: texto o imagen con opacidad configurable.
- **Optimizer**: optimización inteligente automatizada.

---

## Sistema de Traducciones

La aplicación cuenta con un sistema completo de traducciones multiidioma.

### Idiomas disponibles

- **Español** (`es.py`)
- **English** (`en.py`)
- **Português** (`pt.py`)

### Uso

```python
from app.translations import t, set_language, get_language, AVAILABLE_LANGUAGES

# Obtener traducción
texto = t('compress_title')  # returns 'Comprimir' / 'Compress' / 'Comprimir'

# Cambiar idioma
set_language('Español')

# Obtener idioma actual
idioma = get_language()  # returns 'Español', 'English' or 'Português'

# Idiomas disponibles
print(AVAILABLE_LANGUAGES)  # {'Español': 'Español', 'English': 'English', 'Português': 'Português'}
```

### Keys de traducción

El sistema usa un archivo JSON para guardar la configuración del usuario (`app/user_settings.json`).

### Título de la ventana

El título de la ventana también es traducible (`app_title`):

- Español: "Yagua - Procesador de Imágenes"
- English: "Yagua - Image Editor"
- Português: "Yagua - Editor de Imagens"

---

## Contribución

### Convenciones de código

- **PEP 8** para estilo de código
- **type hints** para funciones públicas
- **docstrings** en inglés para funciones, español para UI
- Nombres descriptivos en español para variables de UI

### Nomenclatura de archivos

- `snake_case.py` para módulos
- `PascalCase.py` para clases
- `camelCase` evitado en Python

### Agregar un nuevo módulo

1. Crear la lógica en `app/modules/nombre.py` (opcional)
2. Crear el módulo UI en `app/ui/frames/nombre/` con `frame.py`, `services.py`, `state.py`
3. Registrar en `app/ui/module_registry.py` (label, ícono, frame_import)
4. Agregar ícono en `assets/icons/`
5. Agregar traducciones en `app/translations/es.py`, `en.py`, `pt.py`

### Testing

Para probar un módulo específico:

```bash
python -c "from app.modules.compress import comprimir_imagen; print(comprimir_imagen('input.jpg', 'output.jpg'))"
```

---

## Licencia

MIT License - Ver archivo LICENSE para más detalles.
