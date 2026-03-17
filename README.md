<img width="1761" height="497" alt="banner" src="https://github.com/user-attachments/assets/73597562-cdbd-4780-a0d3-ebe6f74b8603" />

# Yagua - Editor de Imágenes

Aplicación de escritorio para procesar imágenes

---

## Tabla de Contenidos

1. [CaracterÃ­sticas](#caracterÃ­sticas)
2. [Tech Stack](#tech-stack)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Arquitectura](#arquitectura)
5. [MÃ³dulos Implementados](#mÃ³dulos-implementados)
6. [Sistema de Traducciones](#sistema-de-traducciones)
7. [EjecuciÃ³n](#ejecuciÃ³n)
8. [ContribuciÃ³n](#contribuciÃ³n)

---

## CaracterÃ­sticas

- **CompresiÃ³n de imÃ¡genes**: Reduce el tamaÃ±o de imÃ¡genes manteniendo la calidad
- **ConversiÃ³n de formatos**: Convierte entre JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF
- **ExtracciÃ³n de paleta de colores**: Extrae colores dominantes de una imagen
- **GestiÃ³n de metadatos EXIF**: Lee, edita, limpia y exporta metadatos
- **Redimensionar**: Redimensiona por porcentaje, pÃ­xeles o presets (Instagram, Facebook, YouTube, etc.)
- **Recortar**: Recorte centrado con dimensiones personalizadas
- **Canvas**: Ajusta el tamaÃ±o del canvas manteniendo la imagen centrada
- **Renombrar lote**: Renombra mÃºltiples archivos con patrones personalizables
- **Marca de agua**: Agrega texto o imagen como marca de agua
- **Quitar fondo**: Elimina el fondo de imÃ¡genes usando IA (rembg)
- **LQIP**: Genera Low Quality Image Placeholders y Base64
- **Optimizer**: OptimizaciÃ³n inteligente automÃ¡tica
- **Multiidioma**: EspaÃ±ol, English, PortuguÃªs
- **Inicio maximizado**: La app se inicia maximizada por defecto

---

## Tech Stack

| TecnologÃ­a       | VersiÃ³n | PropÃ³sito                            |
| ----------------- | -------- | ------------------------------------- |
| **Python**        | 3.13+    | Lenguaje principal                    |
| **CustomTkinter** | 5.2.2    | Framework de UI moderno               |
| **Pillow**        | 12.1.1   | Procesamiento de imÃ¡genes            |
| **piexif**        | 1.1.3    | ManipulaciÃ³n de metadatos EXIF       |
| **tkinterdnd2**   | 0.4.3    | Drag & Drop                           |
| **darkdetect**    | 0.8.0    | DetecciÃ³n de tema oscuro del sistema |
| **rembg**         | 2.0.57   | RemociÃ³n de fondo con IA             |

### Requisitos del Sistema

- Windows 10/11 (macOS y Linux parcialmente soportados)
- Python 3.13 o superior
- Al menos 4GB de RAM recomendada

---

## Estructura del Proyecto

```
Yagua/
â”œâ”€â”€ main.py                 # Punto de entrada de la aplicaciÃ³n
â”œâ”€â”€ app.py                 # Clase principal YaguaApp
â”œâ”€â”€ user_settings.json     # ConfiguraciÃ³n del usuario (idioma, etc.)
â”œâ”€â”€ core/                  # LÃ³gica de negocio (re-exports)
â”œâ”€â”€ modules/               # MÃ³dulos de procesamiento de imagen
â”‚   â”œâ”€â”€ compress.py        # CompresiÃ³n de imÃ¡genes
â”‚   â”œâ”€â”€ convert.py        # ConversiÃ³n de formatos
â”‚   â”œâ”€â”€ palette.py        # ExtracciÃ³n de paleta de colores
â”‚   â”œâ”€â”€ metadata.py       # GestiÃ³n de metadatos EXIF
â”‚   â””â”€â”€ resize.py         # Redimensionado, recorte y canvas
â”œâ”€â”€ ui/                   # Interfaz de usuario
â”‚   â”œâ”€â”€ main_window.py   # Ventana principal
â”‚   â”œâ”€â”€ sidebar.py       # Barra lateral de navegaciÃ³n
â”‚   â”œâ”€â”€ colors.py        # Paleta de colores del tema
â”‚   â”œâ”€â”€ fonts.py         # ConfiguraciÃ³n de fuentes
â”‚   â”œâ”€â”€ frames/          # Frames de cada mÃ³dulo
â”‚   â”‚   â”œâ”€â”€ base.py                    # Clase base para frames
â”‚   â”‚   â”œâ”€â”€ compress/frame.py          # MÃ³dulo comprimir
â”‚   â”‚   â”œâ”€â”€ convert/frame.py           # MÃ³dulo convertir
â”‚   â”‚   â”œâ”€â”€ palette/frame.py           # MÃ³dulo paleta
â”‚   â”‚   â”œâ”€â”€ metadata/frame.py          # MÃ³dulo metadatos
â”‚   â”‚   â”œâ”€â”€ resize/frame.py            # MÃ³dulo redimensionar
â”‚   â”‚   â”œâ”€â”€ rename_frame.py            # MÃ³dulo renombrar
â”‚   â”‚   â”œâ”€â”€ watermark_frame.py        # MÃ³dulo marca de agua
â”‚   â”‚   â”œâ”€â”€ remove_bg_frame.py        # MÃ³dulo quitar fondo
â”‚   â”‚   â”œâ”€â”€ lqip_frame.py              # MÃ³dulo LQIP
â”‚   â”‚   â”œâ”€â”€ optimizer_frame.py        # MÃ³dulo optimizador
â”‚   â”‚   â””â”€â”€ settings/frame.py         # MÃ³dulo ajustes
â”‚   â””â”€â”€ widgets/         # Componentes UI reutilizables
â”œâ”€â”€ translations/         # Sistema de traducciones
â”‚   â”œâ”€â”€ __init__.py      # Funciones t(), set_language(), get_language()
â”‚   â”œâ”€â”€ es.py            # Traducciones espaÃ±ol
â”‚   â”œâ”€â”€ en.py            # Traducciones inglÃ©s
â”‚   â””â”€â”€ pt.py            # Traducciones portuguÃ©s
â”œâ”€â”€ utils/               # Funciones helper
â”‚   â””â”€â”€ __init__.py      # tintar_icono()
â””â”€â”€ assets/              # Recursos estÃ¡ticos
    â”œâ”€â”€ icon.ico        # Icono de la aplicaciÃ³n (Windows)
    â”œâ”€â”€ icon.png        # Icono de la aplicaciÃ³n
    â”œâ”€â”€ fonts/
    â”‚   â””â”€â”€ Inter.ttf   # Fuente personalizada
    â””â”€â”€ icons/          # Ãconos de la interfaz
```

---

## Arquitectura

### PatrÃ³n de Arquitectura

El proyecto sigue una arquitectura **MVC simplificada** con separaciÃ³n clara de responsabilidades:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                     PRESENTATION LAYER                   â”‚
â”‚  (ui/)                                                  â”‚
â”‚  - frames/          â†’ Vistas (CTkFrame)                 â”‚
â”‚  - main_window.py  â†’ Controlador principal             â”‚
â”‚  - sidebar.py      â†’ NavegaciÃ³n                        â”‚
â”‚  - translations/   â†’ Sistema de traducciones           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
                            â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                     BUSINESS LOGIC LAYER                â”‚
â”‚  (modules/)                                             â”‚
â”‚  - compress.py     â†’ LÃ³gica de compresiÃ³n              â”‚
â”‚  - convert.py      â†’ LÃ³gica de conversiÃ³n              â”‚
â”‚  - palette.py      â†’ ExtracciÃ³n de colores            â”‚
â”‚  - metadata.py     â†’ GestiÃ³n EXIF                     â”‚
â”‚  - resize.py       â†’ Redimensionado y recorte          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
                            â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                       UTILITIES                         â”‚
â”‚  (utils/)                                              â”‚
â”‚  - tintar_icono()  â†’ Helper para Ã­conos                â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Flujo de Datos

1. **Usuario** interactÃºa con la UI (frames)
2. **Frame** invoca mÃ©todo del mÃ³dulo correspondiente en `modules/`
3. **MÃ³dulo** procesa la imagen usando Pillow
4. **Resultado** retorna al frame y se actualiza la UI

### Clases Principales

| Clase           | UbicaciÃ³n                    | Responsabilidad                    |
| --------------- | ----------------------------- | ---------------------------------- |
| `YaguaApp`      | `app.py`                      | Ventana principal, inicializaciÃ³n |
| `MainWindow`    | `ui/main_window.py`           | Contenedor con sidebar y frames    |
| `Sidebar`       | `ui/sidebar.py`               | NavegaciÃ³n entre mÃ³dulos         |
| `BaseFrame`     | `ui/frames/base.py`           | Clase base con mÃ©todos comunes    |
| `SettingsFrame` | `ui/frames/settings/frame.py` | ConfiguraciÃ³n (idioma, tema)      |

---

## MÃ³dulos Implementados

### 1. CompresiÃ³n (`compress.py`)

**Funcionalidades:**

- CompresiÃ³n de imÃ¡genes con calidad configurable (10-100)
- EliminaciÃ³n opcional de metadatos EXIF
- EstimaciÃ³n de tamaÃ±o antes de comprimir
- PreservaciÃ³n del formato original o conversiÃ³n automÃ¡tica
- Soporte para JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF
- Vista previa de imÃ¡genes cargadas

**Funciones pÃºblicas:**

```python
comprimir_imagen(ruta_entrada, ruta_salida, calidad=85, quitar_exif=True) -> dict
estimar_tamano(ruta_entrada, calidad) -> int
formatear_bytes(bytes_val) -> str
```

### 2. ConversiÃ³n (`convert.py`)

**Funcionalidades:**

- ConversiÃ³n entre mÃºltiples formatos
- Calidad configurable por formato
- CorrecciÃ³n automÃ¡tica de modos de color (RGBA â†’ RGB para JPEG)
- Soporte para conversiÃ³n por lotes
- Vista previa de imÃ¡genes cargadas

**Formatos soportados:** JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF

**Funciones pÃºblicas:**

```python
convertir_imagen(ruta_entrada, fmt_destino, carpeta_salida, calidad=90) -> dict
batch_convertir(rutas, fmt_destino, carpeta_salida, calidad=90, progress_cb=None) -> list
```

### 3. Paleta de Colores (`palette.py`)

**Funcionalidades:**

- ExtracciÃ³n de N colores dominantes (4-12)
- ConversiÃ³n de colores a mÃºltiples formatos (HEX, RGB, HSL, CSS)
- ExportaciÃ³n de paleta como imagen PNG
- DetecciÃ³n de luminosidad para texto legible
- Copiar color al portapapeles en diferentes formatos

**Funciones pÃºblicas:**

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
- EdiciÃ³n de campos (Autor, Copyright, Software, Fecha)
- Limpieza de metadatos por lotes
- ExportaciÃ³n a TXT y JSON
- Coordenadas GPS con enlace a Google Maps
- Soporte para JPEG y TIFF

**Funciones pÃºblicas:**

```python
leer_metadatos(ruta) -> dict[str, str]
limpiar_exif(ruta_entrada, ruta_salida) -> dict
editar_exif(ruta_entrada, ruta_salida, campos) -> bool
exportar_txt(metadatos, ruta)
exportar_json(metadatos, ruta)
```

### 5. Redimensionar (`resize.py`)

**Funcionalidades:**

- **Redimensionar**: Por porcentaje o pÃ­xeles, manteniendo relaciÃ³n de aspecto
- **Recortar**: Recorte centrado con dimensiones personalizadas
- **Canvas**: Ajusta el tamaÃ±o del canvas con color de fondo (blanco, negro, transparente)
- **Presets**: Instagram, Facebook, Twitter/X, YouTube, LinkedIn, TikTok, Pinterest, Web, resoluciones estÃ¡ndar e Ã­conos

**Presets disponibles:**

- Instagram: Post cuadrado 1:1, Post portrait 4:5, Story/Reels 9:16
- Facebook: Post 1200Ã—630, Cover 851Ã—315
- Twitter/X: Post 16:9, Header 3:1
- YouTube: Thumbnail 16:9, Channel art 16:9
- LinkedIn: Post 1.91:1, Cover personal 4:1
- TikTok/WhatsApp: Status/Video 9:16
- Pinterest: Pin estÃ¡ndar 2:3
- Web: OG image 1.91:1
- Resoluciones: HD 720p, Full HD 1080p, 2K, 4K UHD
- Ãconos: Favicon 32Ã—32, Ãcono 256, Ãcono 512

### 6. Renombrar Lote (`rename_frame.py`)

**Funcionalidades:**

- Renombrado por prefijo, sufijo o reemplazo de texto
- NumeraciÃ³n secuencial
- Fecha de modificaciÃ³n como parte del nombre
- Preview de los nuevos nombres antes de aplicar

### 7. Marca de Agua (`watermark_frame.py`)

**Funcionalidades:**

- Texto como marca de agua
- Imagen como marca de agua
- Posicionamiento (esquinas, centro, mosaico)
- Opacidad configurable
- TamaÃ±o y Ã¡ngulo ajustables

### 8. Quitar Fondo (`remove_bg_frame.py`)

**Funcionalidades:**

- EliminaciÃ³n de fondo usando IA (rembg)
- Soporte para personas, productos, dibujos, etc.
- ExportaciÃ³n en PNG con transparencia

### 9. LQIP (`lqip_frame.py`)

**Funcionalidades:**

- Genera Low Quality Image Placeholders
- Exporta en Base64
- Vista previa de las miniaturas

### 10. Optimizer (`optimizer_frame.py`)

**Funcionalidades:**

- OptimizaciÃ³n inteligente automÃ¡tica
- CompresiÃ³n automÃ¡tica con detecciÃ³n de mejor calidad
- Procesamiento por lotes

### 11. Settings (`settings/frame.py`)

**Funcionalidades:**

- Cambio de idioma (EspaÃ±ol, English, PortuguÃªs)
- Reinicio automÃ¡tico de la app al cambiar idioma

---

## Sistema de Traducciones

La aplicaciÃ³n cuenta con un sistema completo de traducciones multiidioma.

### Idiomas disponibles

- **EspaÃ±ol** (`es.py`)
- **English** (`en.py`)
- **PortuguÃªs** (`pt.py`)

### Uso

```python
from translations import t, set_language, get_language, AVAILABLE_LANGUAGES

# Obtener traducciÃ³n
texto = t('compress_title')  # returns 'Comprimir' / 'Compress' / 'Comprimir'

# Cambiar idioma
set_language('EspaÃ±ol')

# Obtener idioma actual
idioma = get_language()  # returns 'EspaÃ±ol', 'English' or 'PortuguÃªs'

# Idiomas disponibles
print(AVAILABLE_LANGUAGES)  # {'EspaÃ±ol': 'EspaÃ±ol', 'English': 'English', 'PortuguÃªs': 'PortuguÃªs'}
```

### keys de traducciÃ³n

El sistema usa un archivo JSON para guardar la configuraciÃ³n del usuario (`user_settings.json`).

### Ventana tÃ­tulo

El tÃ­tulo de la ventana tambiÃ©n es traducible (`app_title`):

- EspaÃ±ol: "Yagua - Editor de ImÃ¡genes"
- English: "Yagua - Image Editor"
- PortuguÃªs: "Yagua - Editor de Imagens"

---

## EjecuciÃ³n

### InstalaciÃ³n de dependencias

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install customtkinter==5.2.2 pillow==12.1.1 piexif==1.1.3 tkinterdnd2==0.4.3 rembg==2.0.57
```

### Ejecutar la aplicaciÃ³n

```bash
python main.py
```

### Estructura de temas

La aplicaciÃ³n usa tema oscuro por defecto. Los colores estÃ¡n definidos en `ui/colors.py`:

```python
FRAMES_BG = '#0A0A0B'      # Fondo principal
SIDEBAR_BG = '#121214'      # Fondo del sidebar
PANEL_BG = '#1C1C1E'        # Fondo de paneles
TEXT_COLOR = '#F2F2F7'     # Color de texto principal
ACENTO = '#FFFFFF'          # Color de acento
```

### Inicio maximizado

La aplicaciÃ³n se inicia maximizada automÃ¡ticamente usando `self.state('zoomed')` en Windows.

---

## ContribuciÃ³n

### Convenciones de cÃ³digo

- **PEP 8** para estilo de cÃ³digo
- **type hints** para funciones pÃºblicas
- **docstrings** en inglÃ©s para funciones, espaÃ±ol para UI
- Nombres descriptivos en espaÃ±ol para variables de UI

### Nomenclatura de archivos

- `snake_case.py` para mÃ³dulos
- `PascalCase.py` para clases
- `camelCase` evitado en Python

### Agregar un nuevo mÃ³dulo

1. Crear la lÃ³gica en `modules/nombre.py` (opcional)
2. Crear el frame en `ui/frames/nombre_frame.py`
3. Registrar en `ui/main_window.py` â†’ `MODULOS`
4. Agregar Ã­cono en `assets/icons/`
5. Agregar traducciones en `translations/es.py`, `en.py`, `pt.py`
6. Agregar entrada de menÃº en `ui/sidebar.py` â†’ `MENU_ITEMS`

### Testing

Para probar un mÃ³dulo especÃ­fico:

```bash
python -c "from modules.compress import comprimir_imagen; print(comprimir_imagen('input.jpg', 'output.jpg'))"
```

---

## Licencia

MIT License - Ver archivo LICENSE para mÃ¡s detalles.
