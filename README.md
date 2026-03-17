<img width="1761" height="497" alt="banner" src="https://github.com/user-attachments/assets/73597562-cdbd-4780-a0d3-ebe6f74b8603" />

# Yagua - Editor de ImÃ¡genes

AplicaciÃ³n de escritorio para procesar imÃ¡genes

---

## Tabla de Contenidos

1. [CaracterÃƒÂ­sticas](#caracterÃƒÂ­sticas)
2. [Tech Stack](#tech-stack)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Arquitectura](#arquitectura)
5. [MÃƒÂ³dulos Implementados](#mÃƒÂ³dulos-implementados)
6. [Sistema de Traducciones](#sistema-de-traducciones)
7. [EjecuciÃƒÂ³n](#ejecuciÃƒÂ³n)
8. [ContribuciÃƒÂ³n](#contribuciÃƒÂ³n)

---

## CaracterÃƒÂ­sticas

- **CompresiÃƒÂ³n de imÃƒÂ¡genes**: Reduce el tamaÃƒÂ±o de imÃƒÂ¡genes manteniendo la calidad
- **ConversiÃƒÂ³n de formatos**: Convierte entre JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF
- **ExtracciÃƒÂ³n de paleta de colores**: Extrae colores dominantes de una imagen
- **GestiÃƒÂ³n de metadatos EXIF**: Lee, edita, limpia y exporta metadatos
- **Redimensionar**: Redimensiona por porcentaje, pÃƒÂ­xeles o presets (Instagram, Facebook, YouTube, etc.)
- **Recortar**: Recorte centrado con dimensiones personalizadas
- **Canvas**: Ajusta el tamaÃƒÂ±o del canvas manteniendo la imagen centrada
- **Renombrar lote**: Renombra mÃƒÂºltiples archivos con patrones personalizables
- **Marca de agua**: Agrega texto o imagen como marca de agua
- **Quitar fondo**: Elimina el fondo de imÃƒÂ¡genes usando IA (rembg)
- **LQIP**: Genera Low Quality Image Placeholders y Base64
- **Optimizer**: OptimizaciÃƒÂ³n inteligente automÃƒÂ¡tica
- **Multiidioma**: EspaÃƒÂ±ol, English, PortuguÃƒÂªs
- **Inicio maximizado**: La app se inicia maximizada por defecto

---

## Tech Stack

| TecnologÃƒÂ­a       | VersiÃƒÂ³n | PropÃƒÂ³sito                            |
| ----------------- | -------- | ------------------------------------- |
| **Python**        | 3.13+    | Lenguaje principal                    |
| **CustomTkinter** | 5.2.2    | Framework de UI moderno               |
| **Pillow**        | 12.1.1   | Procesamiento de imÃƒÂ¡genes            |
| **piexif**        | 1.1.3    | ManipulaciÃƒÂ³n de metadatos EXIF       |
| **tkinterdnd2**   | 0.4.3    | Drag & Drop                           |
| **darkdetect**    | 0.8.0    | DetecciÃƒÂ³n de tema oscuro del sistema |
| **rembg**         | 2.0.57   | RemociÃƒÂ³n de fondo con IA             |

### Requisitos del Sistema

- Windows 10/11 (macOS y Linux parcialmente soportados)
- Python 3.13 o superior
- Al menos 4GB de RAM recomendada

---

## Estructura del Proyecto

```
Yagua/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ main.py                    # Entry point de compatibilidad
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ app/                        # CÃ³digo de la aplicaciÃƒÂ³n
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ main.py             # Punto de entrada de la aplicaciÃƒÂ³n
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ app.py              # Clase principal YaguaApp
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ user_settings.json  # ConfiguraciÃƒÂ³n del usuario (idioma, etc.)
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ core/               # LÃƒÂ³gica de negocio (re-exports)
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ modules/            # MÃƒÂ³dulos de procesamiento de imagen
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ compress.py        # CompresiÃƒÂ³n de imÃƒÂ¡genes
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ convert.py        # ConversiÃƒÂ³n de formatos
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ palette.py        # ExtracciÃƒÂ³n de paleta de colores
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ metadata.py       # GestiÃƒÂ³n de metadatos EXIF
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ resize.py         # Redimensionado, recorte y canvas
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ ui/                 # Interfaz de usuario
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ main_window.py   # Ventana principal
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ sidebar.py       # Barra lateral de navegaciÃƒÂ³n
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ module_registry.py  # Registro central de mÃ³dulos
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ colors.py        # Paleta de colores del tema
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ fonts.py         # ConfiguraciÃƒÂ³n de fuentes
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ frames/          # Frames de cada mÃƒÂ³dulo
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ base.py                 # Clase base para frames
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ compress/               # MÃ³dulo comprimir
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ frame.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ services.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ state.py
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ convert/                # MÃ³dulo convertir (frame/services/state)
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ palette/                # MÃ³dulo paleta (frame/services/state)
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ metadata/               # MÃ³dulo metadatos (frame/services/state)
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ resize/                 # MÃ³dulo redimensionar (frame/services/state)
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ settings/               # MÃ³dulo ajustes (frame/services/state)
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ rename_frame.py         # MÃ³dulo renombrar
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ watermark_frame.py     # MÃ³dulo marca de agua
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ remove_bg_frame.py     # MÃ³dulo quitar fondo
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ lqip_frame.py           # MÃ³dulo LQIP
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ optimizer_frame.py     # MÃ³dulo optimizador
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ placeholder_frame.py   # Placeholder base
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ translations/       # Sistema de traducciones
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py      # Funciones t(), set_language(), get_language()
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ es.py            # Traducciones espaÃƒÂ±ol
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ en.py            # Traducciones inglÃƒÂ©s
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ pt.py            # Traducciones portuguÃƒÂ©s
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ utils/               # Funciones helper
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ __init__.py      # tintar_icono()
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ assets/                    # Recursos estÃƒÂ¡ticos
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ docs/                      # DocumentaciÃƒÂ³n (QA checklist)
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ icon.ico        # Icono de la aplicaciÃƒÂ³n (Windows)
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ icon.png        # Icono de la aplicaciÃƒÂ³n
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ fonts/
    Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ Inter.ttf   # Fuente personalizada
    Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ icons/          # ÃƒÂconos de la interfaz
```

---

## Arquitectura

### PatrÃƒÂ³n de Arquitectura

El proyecto sigue una arquitectura **MVC simplificada** con separaciÃƒÂ³n clara de responsabilidades:

```
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š                     PRESENTATION LAYER                   Ã¢â€â€š
Ã¢â€â€š  (app/ui/)                                                  Ã¢â€â€š
Ã¢â€â€š  - frames/          Ã¢â€ â€™ Vistas (CTkFrame)                 Ã¢â€â€š
Ã¢â€â€š  - main_window.py  Ã¢â€ â€™ Controlador principal             Ã¢â€â€š
Ã¢â€â€š  - sidebar.py      Ã¢â€ â€™ NavegaciÃƒÂ³n                        Ã¢â€â€š
Ã¢â€â€š  - app/translations/   Ã¢â€ â€™ Sistema de traducciones           Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
                            Ã¢â€â€š
                            Ã¢â€“Â¼
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š                     BUSINESS LOGIC LAYER                Ã¢â€â€š
Ã¢â€â€š  (app/modules/)                                             Ã¢â€â€š
Ã¢â€â€š  - compress.py     Ã¢â€ â€™ LÃƒÂ³gica de compresiÃƒÂ³n              Ã¢â€â€š
Ã¢â€â€š  - convert.py      Ã¢â€ â€™ LÃƒÂ³gica de conversiÃƒÂ³n              Ã¢â€â€š
Ã¢â€â€š  - palette.py      Ã¢â€ â€™ ExtracciÃƒÂ³n de colores            Ã¢â€â€š
Ã¢â€â€š  - metadata.py     Ã¢â€ â€™ GestiÃƒÂ³n EXIF                     Ã¢â€â€š
Ã¢â€â€š  - resize.py       Ã¢â€ â€™ Redimensionado y recorte          Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
                            Ã¢â€â€š
                            Ã¢â€“Â¼
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š                       UTILITIES                         Ã¢â€â€š
Ã¢â€â€š  (app/utils/)                                              Ã¢â€â€š
Ã¢â€â€š  - tintar_icono()  Ã¢â€ â€™ Helper para ÃƒÂ­conos                Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
```

### Flujo de Datos

1. **Usuario** interactÃƒÂºa con la UI (frames)
2. **Frame** invoca funciones de `services.py` del mÃƒÂ³dulo
3. **Services** delega en `app/modules/` para el procesamiento con Pillow
4. **Resultado** retorna al frame y se actualiza la UI

### Clases Principales

| Clase           | UbicaciÃƒÂ³n                    | Responsabilidad                    |
| --------------- | ----------------------------- | ---------------------------------- |
| `YaguaApp`      | `app/app.py`                         | Ventana principal, inicializaciÃƒÂ³n |
| `MainWindow`    | `app/ui/main_window.py`              | Contenedor con sidebar y frames     |
| `Sidebar`       | `app/ui/sidebar.py`                  | NavegaciÃƒÂ³n entre mÃƒÂ³dulos          |
| `ModuleRegistry`| `app/ui/module_registry.py`          | Registro central de mÃƒÂ³dulos         |
| `BaseFrame`     | `app/ui/frames/base.py`              | Clase base con mÃƒÂ©todos comunes     |
| `SettingsFrame` | `app/ui/frames/settings/frame.py`    | ConfiguraciÃƒÂ³n (idioma, tema)       |

---

## MÃƒÂ³dulos Implementados

### 1. CompresiÃƒÂ³n (`compress.py`)

**Funcionalidades:**

- CompresiÃƒÂ³n de imÃƒÂ¡genes con calidad configurable (10-100)
- EliminaciÃƒÂ³n opcional de metadatos EXIF
- EstimaciÃƒÂ³n de tamaÃƒÂ±o antes de comprimir
- PreservaciÃƒÂ³n del formato original o conversiÃƒÂ³n automÃƒÂ¡tica
- Soporte para JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF
- Vista previa de imÃƒÂ¡genes cargadas

**Funciones pÃƒÂºblicas:**

```python
comprimir_imagen(ruta_entrada, ruta_salida, calidad=85, quitar_exif=True) -> dict
estimar_tamano(ruta_entrada, calidad) -> int
formatear_bytes(bytes_val) -> str
```

### 2. ConversiÃƒÂ³n (`convert.py`)

**Funcionalidades:**

- ConversiÃƒÂ³n entre mÃƒÂºltiples formatos
- Calidad configurable por formato
- CorrecciÃƒÂ³n automÃƒÂ¡tica de modos de color (RGBA Ã¢â€ â€™ RGB para JPEG)
- Soporte para conversiÃƒÂ³n por lotes
- Vista previa de imÃƒÂ¡genes cargadas

**Formatos soportados:** JPEG, PNG, WEBP, AVIF, ICO, BMP, TIFF, GIF

**Funciones pÃƒÂºblicas:**

```python
convertir_imagen(ruta_entrada, fmt_destino, carpeta_salida, calidad=90) -> dict
batch_convertir(rutas, fmt_destino, carpeta_salida, calidad=90, progress_cb=None) -> list
```

### 3. Paleta de Colores (`palette.py`)

**Funcionalidades:**

- ExtracciÃƒÂ³n de N colores dominantes (4-12)
- ConversiÃƒÂ³n de colores a mÃƒÂºltiples formatos (HEX, RGB, HSL, CSS)
- ExportaciÃƒÂ³n de paleta como imagen PNG
- DetecciÃƒÂ³n de luminosidad para texto legible
- Copiar color al portapapeles en diferentes formatos

**Funciones pÃƒÂºblicas:**

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
- EdiciÃƒÂ³n de campos (Autor, Copyright, Software, Fecha)
- Limpieza de metadatos por lotes
- ExportaciÃƒÂ³n a TXT y JSON
- Coordenadas GPS con enlace a Google Maps
- Soporte para JPEG y TIFF

**Funciones pÃƒÂºblicas:**

```python
leer_metadatos(ruta) -> dict[str, str]
limpiar_exif(ruta_entrada, ruta_salida) -> dict
editar_exif(ruta_entrada, ruta_salida, campos) -> bool
exportar_txt(metadatos, ruta)
exportar_json(metadatos, ruta)
```

### 5. Redimensionar (`resize.py`)

**Funcionalidades:**

- **Redimensionar**: Por porcentaje o pÃƒÂ­xeles, manteniendo relaciÃƒÂ³n de aspecto
- **Recortar**: Recorte centrado con dimensiones personalizadas
- **Canvas**: Ajusta el tamaÃƒÂ±o del canvas con color de fondo (blanco, negro, transparente)
- **Presets**: Instagram, Facebook, Twitter/X, YouTube, LinkedIn, TikTok, Pinterest, Web, resoluciones estÃƒÂ¡ndar e ÃƒÂ­conos

**Presets disponibles:**

- Instagram: Post cuadrado 1:1, Post portrait 4:5, Story/Reels 9:16
- Facebook: Post 1200Ãƒâ€”630, Cover 851Ãƒâ€”315
- Twitter/X: Post 16:9, Header 3:1
- YouTube: Thumbnail 16:9, Channel art 16:9
- LinkedIn: Post 1.91:1, Cover personal 4:1
- TikTok/WhatsApp: Status/Video 9:16
- Pinterest: Pin estÃƒÂ¡ndar 2:3
- Web: OG image 1.91:1
- Resoluciones: HD 720p, Full HD 1080p, 2K, 4K UHD
- ÃƒÂconos: Favicon 32Ãƒâ€”32, ÃƒÂcono 256, ÃƒÂcono 512

### 6. Renombrar Lote (`rename_frame.py`)

**Funcionalidades:**

- Renombrado por prefijo, sufijo o reemplazo de texto
- NumeraciÃƒÂ³n secuencial
- Fecha de modificaciÃƒÂ³n como parte del nombre
- Preview de los nuevos nombres antes de aplicar

### 7. Marca de Agua (`watermark_frame.py`)

**Funcionalidades:**

- Texto como marca de agua
- Imagen como marca de agua
- Posicionamiento (esquinas, centro, mosaico)
- Opacidad configurable
- TamaÃƒÂ±o y ÃƒÂ¡ngulo ajustables

### 8. Quitar Fondo (`remove_bg_frame.py`)

**Funcionalidades:**

- EliminaciÃƒÂ³n de fondo usando IA (rembg)
- Soporte para personas, productos, dibujos, etc.
- ExportaciÃƒÂ³n en PNG con transparencia

### 9. LQIP (`lqip_frame.py`)

**Funcionalidades:**

- Genera Low Quality Image Placeholders
- Exporta en Base64
- Vista previa de las miniaturas

### 10. Optimizer (`optimizer_frame.py`)

**Funcionalidades:**

- OptimizaciÃƒÂ³n inteligente automÃƒÂ¡tica
- CompresiÃƒÂ³n automÃƒÂ¡tica con detecciÃƒÂ³n de mejor calidad
- Procesamiento por lotes

### 11. Settings (`settings/frame.py`)

**Funcionalidades:**

- Cambio de idioma (EspaÃƒÂ±ol, English, PortuguÃƒÂªs)
- Reinicio automÃƒÂ¡tico de la app al cambiar idioma

---

## Sistema de Traducciones

La aplicaciÃƒÂ³n cuenta con un sistema completo de traducciones multiidioma.

### Idiomas disponibles

- **EspaÃƒÂ±ol** (`es.py`)
- **English** (`en.py`)
- **PortuguÃƒÂªs** (`pt.py`)

### Uso

```python
from app.translations import t, set_language, get_language, AVAILABLE_LANGUAGES

# Obtener traducciÃƒÂ³n
texto = t('compress_title')  # returns 'Comprimir' / 'Compress' / 'Comprimir'

# Cambiar idioma
set_language('EspaÃƒÂ±ol')

# Obtener idioma actual
idioma = get_language()  # returns 'EspaÃƒÂ±ol', 'English' or 'PortuguÃƒÂªs'

# Idiomas disponibles
print(AVAILABLE_LANGUAGES)  # {'EspaÃƒÂ±ol': 'EspaÃƒÂ±ol', 'English': 'English', 'PortuguÃƒÂªs': 'PortuguÃƒÂªs'}
```

### keys de traducciÃƒÂ³n

El sistema usa un archivo JSON para guardar la configuraciÃƒÂ³n del usuario (`app/user_settings.json`).

### Ventana tÃƒÂ­tulo

El tÃƒÂ­tulo de la ventana tambiÃƒÂ©n es traducible (`app_title`):

- EspaÃƒÂ±ol: "Yagua - Editor de ImÃƒÂ¡genes"
- English: "Yagua - Image Editor"
- PortuguÃƒÂªs: "Yagua - Editor de Imagens"

---

## EjecuciÃƒÂ³n

### InstalaciÃƒÂ³n de dependencias

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install customtkinter==5.2.2 pillow==12.1.1 piexif==1.1.3 tkinterdnd2==0.4.3 rembg==2.0.57
```

### Ejecutar la aplicaciÃƒÂ³n

```bash
python -m app.main
```

O usando el entrypoint de compatibilidad:

```bash
python main.py
```

### Estructura de temas

La aplicaciÃƒÂ³n usa tema oscuro por defecto. Los colores estÃƒÂ¡n definidos en `app/ui/colors.py`:

```python
FRAMES_BG = '#0A0A0B'      # Fondo principal
SIDEBAR_BG = '#121214'      # Fondo del sidebar
PANEL_BG = '#1C1C1E'        # Fondo de paneles
TEXT_COLOR = '#F2F2F7'     # Color de texto principal
ACENTO = '#FFFFFF'          # Color de acento
```

### Inicio maximizado

La aplicaciÃƒÂ³n se inicia maximizada automÃƒÂ¡ticamente usando `self.state('zoomed')` en Windows.

---

## ContribuciÃƒÂ³n

### Convenciones de cÃƒÂ³digo

- **PEP 8** para estilo de cÃƒÂ³digo
- **type hints** para funciones pÃƒÂºblicas
- **docstrings** en inglÃƒÂ©s para funciones, espaÃƒÂ±ol para UI
- Nombres descriptivos en espaÃƒÂ±ol para variables de UI

### Nomenclatura de archivos

- `snake_case.py` para mÃƒÂ³dulos
- `PascalCase.py` para clases
- `camelCase` evitado en Python

### Agregar un nuevo mÃƒÂ³dulo

1. Crear la lÃƒÂ³gica en `app/modules/nombre.py` (opcional)
2. Crear el mÃƒÂ³dulo UI en `app/ui/frames/nombre/` con `frame.py`, `services.py`, `state.py`
3. Registrar en `app/ui/module_registry.py` (label, icono, frame_import)
4. Agregar ÃƒÂ­cono en `assets/icons/`
5. Agregar traducciones en `app/translations/es.py`, `en.py`, `pt.py`

### Testing

Para probar un mÃƒÂ³dulo especÃƒÂ­fico:

```bash
python -c "from app.modules.compress import comprimir_imagen; print(comprimir_imagen('input.jpg', 'output.jpg'))"
```

---

## Licencia

MIT License - Ver archivo LICENSE para mÃƒÂ¡s detalles.
