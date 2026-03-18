# Yagua - Editor de Imagenes

Aplicacion de escritorio para procesar imagenes

---

## Tabla de Contenidos

1. [Caracteristicas](#caracteristicas)
2. [Tech Stack](#tech-stack)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Arquitectura](#arquitectura)
5. [Modulos Implementados](#modulos-implementados)
6. [Sistema de Traducciones](#sistema-de-traducciones)
7. [Ejecucion](#ejecucion)
8. [Contribucion](#contribucion)

---

## Caracteristicas

- **Compresion de imagenes**: Reduce el tamano de imagenes manteniendo la calidad
- **Conversion de formatos**: Convierte entre JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF
- **Extraccion de paleta de colores**: Extrae colores dominantes de una imagen
- **Gestion de metadatos EXIF**: Lee, edita, limpia y exporta metadatos
- **Redimensionar**: Redimensiona por porcentaje, pixeles o presets (Instagram, Facebook, YouTube, etc.)
- **Recortar**: Recorte centrado con dimensiones personalizadas
- **Canvas**: Ajusta el tamano del canvas manteniendo la imagen centrada
- **Renombrar lote**: Renombra multiples archivos con patrones personalizables
- **Marca de agua**: Agrega texto o imagen como marca de agua
- **Quitar fondo**: Elimina el fondo de imagenes usando IA (rembg)
- **LQIP**: Genera Low Quality Image Placeholders y Base64
- **Optimizer**: Optimizacion inteligente automatica
- **Multiidioma**: Espanol, English, Portugues
- **Inicio maximizado**: La app se inicia maximizada por defecto

---

## Tech Stack

| Tecnologia        | Version | Proposito                            |
| ----------------- | -------- | ------------------------------------- |
| **Python**        | 3.13+    | Lenguaje principal                    |
| **CustomTkinter** | 5.2.2    | Framework de UI moderno               |
| **Pillow**        | 12.1.1   | Procesamiento de imagenes             |
| **piexif**        | 1.1.3    | Manipulacion de metadatos EXIF       |
| **tkinterdnd2**   | 0.4.3    | Drag & Drop                           |
| **darkdetect**    | 0.8.0    | Deteccion de tema oscuro del sistema |
| **rembg**         | 2.0.57   | Remocion de fondo con IA             |

### Requisitos del Sistema

- Windows 10/11 (macOS y Linux parcialmente soportados)
- Python 3.13 o superior
- Al menos 4GB de RAM recomendada

---

## Estructura del Proyecto

```
Yagua/
├── main.py                    # Punto de entrada de compatibilidad
├── app/                      # Codigo de la aplicacion
│   ├── main.py               # Punto de entrada de la aplicacion
│   ├── app.py                # Clase principal YaguaApp
│   ├── user_settings.json    # Configuracion del usuario (idioma, etc.)
│   ├── core/                 # Logica de negocio (re-exports)
│   ├── modules/              # Modulos de procesamiento de imagen
│   │   ├── compress.py       # Compresion de imagenes
│   │   ├── convert.py       # Conversion de formatos
│   │   ├── palette.py       # Extraccion de paleta de colores
│   │   ├── metadata.py      # Gestion de metadatos EXIF
│   │   └── resize.py        # Redimensionado, recorte y canvas
│   ├── ui/                   # Interfaz de usuario
│   │   ├── main_window.py   # Ventana principal
│   │   ├── sidebar.py       # Barra lateral de navegacion
│   │   ├── colors.py        # Paleta de colores del tema
│   │   ├── fonts.py         # Configuracion de fuentes
│   │   └── frames/          # Frames de cada modulo
│   │       ├── base.py                    # Clase base para frames
│   │       ├── compress/                  # Modulo comprimir
│   │       ├── convert/                   # Modulo convertir
│   │       ├── palette/                   # Modulo paleta
│   │       ├── metadata/                  # Modulo metadatos
│   │       ├── resize/                    # Modulo redimensionar
│   │       ├── settings/                  # Modulo ajustes
│   │       ├── rename_frame.py            # Modulo renombrar
│   │       ├── watermark_frame.py         # Modulo marca de agua
│   │       ├── remove_bg_frame.py         # Modulo quitar fondo
│   │       ├── lqip_frame.py              # Modulo LQIP
│   │       ├── optimizer_frame.py         # Modulo optimizador
│   │       └── placeholder_frame.py       # Placeholder base
│   ├── translations/         # Sistema de traducciones
│   │   ├── __init__.py      # Funciones t(), set_language(), get_language()
│   │   ├── es.py            # Traducciones espanol
│   │   ├── en.py            # Traducciones ingles
│   │   └── pt.py            # Traducciones portugues
│   └── utils/               # Funciones helper
│       └── __init__.py      # tintar_icono()
└── assets/                  # Recursos estaticos
    ├── icon.ico             # Icono de la aplicacion (Windows)
    ├── icon.png             # Icono de la aplicacion
    ├── fonts/
    │   └── Inter.ttf        # Fuente personalizada
    └── icons/               # Iconos de la interfaz
```

---

## Arquitectura

### Patron de Arquitectura

El proyecto sigue una arquitectura **MVC simplificada** con separacion clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                   │
│  (app/ui/)                                              │
│  - frames/          → Vistas (CTkFrame)                 │
│  - main_window.py  → Controlador principal             │
│  - sidebar.py       → Navegacion                        │
│  - translations/    → Sistema de traducciones           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                │
│  (app/modules/)                                        │
│  - compress.py     → Logica de compresion               │
│  - convert.py      → Logica de conversion               │
│  - palette.py      → Extraccion de colores             │
│  - metadata.py     → Gestion EXIF                       │
│  - resize.py       → Redimensionado y recorte           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                       UTILITIES                         │
│  (app/utils/)                                          │
│  - tintar_icono()  → Helper para iconos                │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Datos

1. **Usuario** interactua con la UI (frames)
2. **Frame** invoca funciones de `services.py` del modulo
3. **Services** delega en `app/modules/` para el procesamiento con Pillow
4. **Resultado** retorna al frame y se actualiza la UI

### Clases Principales

| Clase           | Ubicacion                     | Responsabilidad                    |
| --------------- | ----------------------------- | ---------------------------------- |
| `YaguaApp`      | `app/app.py`                  | Ventana principal, inicializacion  |
| `MainWindow`    | `app/ui/main_window.py`       | Contenedor con sidebar y frames    |
| `Sidebar`       | `app/ui/sidebar.py`           | Navegacion entre modulos           |
| `ModuleRegistry`| `app/ui/module_registry.py`   | Registro central de modulos        |
| `BaseFrame`     | `app/ui/frames/base.py`       | Clase base con metodos comunes     |
| `SettingsFrame` | `app/ui/frames/settings/`     | Configuracion (idioma, tema)       |

---

## Modulos Implementados

### 1. Compresion (`compress.py`)

**Funcionalidades:**

- Compresion de imagenes con calidad configurable (10-100)
- Eliminacion opcional de metadatos EXIF
- Estimacion de tamano antes de comprimir
- Preservacion del formato original o conversion automatica
- Soporte para JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF
- Vista previa de imagenes cargadas

**Funciones publicas:**

```python
comprimir_imagen(ruta_entrada, ruta_salida, calidad=85, quitar_exif=True) -> dict
estimar_tamano(ruta_entrada, calidad) -> int
formatear_bytes(bytes_val) -> str
```

### 2. Conversion (`convert.py`)

**Funcionalidades:**

- Conversion entre multiples formatos
- Calidad configurable por formato
- Correccion automatica de modos de color (RGBA → RGB para JPEG)
- Soporte para conversion por lotes
- Vista previa de imagenes cargadas

**Formatos soportados:** JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF

**Funciones publicas:**

```python
convertir_imagen(ruta_entrada, fmt_destino, carpeta_salida, calidad=90) -> dict
batch_convertir(rutas, fmt_destino, carpeta_salida, calidad=90, progress_cb=None) -> list
```

### 3. Paleta de Colores (`palette.py`)

**Funcionalidades:**

- Extraccion de N colores dominantes (4-12)
- Conversion de colores a multiples formatos (HEX, RGB, HSL, CSS)
- Exportacion de paleta como imagen PNG
- Deteccion de luminosidad para texto legible
- Copiar color al portapapeles en diferentes formatos

**Funciones publicas:**

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
- Edicion de campos (Autor, Copyright, Software, Fecha)
- Limpieza de metadatos por lotes
- Exportacion a TXT y JSON
- Coordenadas GPS con enlace a Google Maps
- Soporte para JPEG y TIFF

**Funciones publicas:**

```python
leer_metadatos(ruta) -> dict[str, str]
limpiar_exif(ruta_entrada, ruta_salida) -> dict
editar_exif(ruta_entrada, ruta_salida, campos) -> bool
exportar_txt(metadatos, ruta)
exportar_json(metadatos, ruta)
```

### 5. Redimensionar (`resize.py`)

**Funcionalidades:**

- **Redimensionar**: Por porcentaje o pixeles, manteniendo relacion de aspecto
- **Recortar**: Recorte centrado con dimensiones personalizadas
- **Canvas**: Ajusta el tamano del canvas con color de fondo (blanco, negro, transparente)
- **Presets**: Instagram, Facebook, Twitter/X, YouTube, LinkedIn, TikTok, Pinterest, Web, resoluciones estandar e iconos

**Presets disponibles:**

- Instagram: Post cuadrado 1:1, Post portrait 4:5, Story/Reels 9:16
- Facebook: Post 1200×630, Cover 851×315
- Twitter/X: Post 16:9, Header 3:1
- YouTube: Thumbnail 16:9, Channel art 16:9
- LinkedIn: Post 1.91:1, Cover personal 4:1
- TikTok/WhatsApp: Status/Video 9:16
- Pinterest: Pin estandar 2:3
- Web: OG image 1.91:1
- Resoluciones: HD 720p, Full HD 1080p, 2K, 4K UHD
- Iconos: Favicon 32×32, Icono 256, Icono 512

### 6. Renombrar Lote (`rename_frame.py`)

**Funcionalidades:**

- Renombrado por prefijo, sufijo o reemplazo de texto
- Numeracion secuencial
- Fecha de modificacion como parte del nombre
- Preview de los nuevos nombres antes de aplicar

### 7. Marca de Agua (`watermark_frame.py`)

**Funcionalidades:**

- Texto como marca de agua
- Imagen como marca de agua
- Posicionamiento (esquinas, centro, mosaico)
- Opacidad configurable
- Tamano y angulo ajustables

### 8. Quitar Fondo (`remove_bg_frame.py`)

**Funcionalidades:**

- Eliminacion de fondo usando IA (rembg)
- Soporte para personas, productos, dibujos, etc.
- Exportacion en PNG con transparencia

### 9. LQIP (`lqip_frame.py`)

**Funcionalidades:**

- Genera Low Quality Image Placeholders
- Exporta en Base64
- Vista previa de las miniaturas

### 10. Optimizer (`optimizer_frame.py`)

**Funcionalidades:**

- Optimizacion inteligente automatica
- Compresion automatica con deteccion de mejor calidad
- Procesamiento por lotes

### 11. Settings (`settings/frame.py`)

**Funcionalidades:**

- Cambio de idioma (Espanol, English, Portugues)
- Reinicio automatico de la app al cambiar idioma

---

## Sistema de Traducciones

La aplicacion cuenta con un sistema completo de traducciones multiidioma.

### Idiomas disponibles

- **Espanol** (`es.py`)
- **English** (`en.py`)
- **Portugues** (`pt.py`)

### Uso

```python
from app.translations import t, set_language, get_language, AVAILABLE_LANGUAGES

# Obtener traduccion
texto = t('compress_title')  # returns 'Comprimir' / 'Compress' / 'Comprimir'

# Cambiar idioma
set_language('Espanol')

# Obtener idioma actual
idioma = get_language()  # returns 'Espanol', 'English' or 'Portugues'

# Idiomas disponibles
print(AVAILABLE_LANGUAGES)  # {'Espanol': 'Espanol', 'English': 'English', 'Portugues': 'Portugues'}
```

### Keys de traduccion

El sistema usa un archivo JSON para guardar la configuracion del usuario (`app/user_settings.json`).

### Ventana titulo

El titulo de la ventana tambien es traducible (`app_title`):

- Espanol: "Yagua - Procesador de Imagenes"
- English: "Yagua - Image Editor"
- Portugues: "Yagua - Editor de Imagens"

---

## Ejecucion

### Instalacion de dependencias

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install customtkinter==5.2.2 pillow==12.1.1 piexif==1.1.3 tkinterdnd2==0.4.3 rembg==2.0.57
```

### Ejecutar la aplicacion

```bash
python -m app.main
```

O usando el entrypoint de compatibilidad:

```bash
python main.py
```

### Estructura de temas

La aplicacion usa tema oscuro por defecto. Los colores estan definidos en `app/ui/colors.py`:

```python
FRAMES_BG = '#0A0A0B'      # Fondo principal
SIDEBAR_BG = '#121214'      # Fondo del sidebar
PANEL_BG = '#1C1C1E'        # Fondo de paneles
TEXT_COLOR = '#F2F2F7'      # Color de texto principal
ACENTO = '#FFFFFF'          # Color de acento
```

### Inicio maximizado

La aplicacion se inicia maximizada automaticamente usando `self.state('zoomed')` en Windows.

---

## Contribucion

### Convenciones de codigo

- **PEP 8** para estilo de codigo
- **type hints** para funciones publicas
- **docstrings** en ingles para funciones, espanol para UI
- Nombres descriptivos en espanol para variables de UI

### Nomenclatura de archivos

- `snake_case.py` para modulos
- `PascalCase.py` para clases
- `camelCase` evitado en Python

### Agregar un nuevo modulo

1. Crear la logica en `app/modules/nombre.py` (opcional)
2. Crear el modulo UI en `app/ui/frames/nombre/` con `frame.py`, `services.py`, `state.py`
3. Registrar en `app/ui/module_registry.py` (label, icono, frame_import)
4. Agregar icono en `assets/icons/`
5. Agregar traducciones en `app/translations/es.py`, `en.py`, `pt.py`

### Testing

Para probar un modulo especifico:

```bash
python -c "from app.modules.compress import comprimir_imagen; print(comprimir_imagen('input.jpg', 'output.jpg'))"
```

---

## Licencia

MIT License - Ver archivo LICENSE para mas detalles.
