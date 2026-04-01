<img width="1761" height="497" alt="banner" src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" />

# Yagua - Procesador de Imagenes

Aplicacion de escritorio para procesar imagenes en lote de forma rapida y elegante. Pensada para flujos de trabajo reales: compresion, conversion, quitar fondo con IA, metadatos EXIF, OCR y marcas de agua.

<a href="https://www.paypal.com/paypalme/guillebouix?locale.x=es_XC&country.x=AR" target="_blank"><img width="300" alt="paypal_donate_button" src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" />
</a>

## Descripcion

Yagua es una app de escritorio gratuita y open source que corre todo localmente. Esta pensada para desarrolladores web, disenadores, fotografos y cualquier usuario que necesite procesar imagenes en lote sin depender de un navegador.

## Features

- Compresion inteligente con control de calidad
- Conversion entre multiples formatos (incluye HEIC/HEIF)
- Eliminacion de fondo con IA (rembg)
- Extracción de texto de imágenes (OCR)
- Marca de agua en lote con preview
- Vectorizacion a SVG
- Edicion/transformacion de imagenes
- Redimensionado, recorte y edicion en canvas
- Extraccion de paleta de colores
- Renombrado masivo con vista previa
- Gestion de metadatos EXIF (ver, editar, limpiar)
- Generacion de LQIP y codificacion Base64
- Soporte multi-idioma (ES / EN / PT)
- Temas oscuros predefinidos

## Instalacion

### Instalacion (Windows)
1. Descargar `Yagua_Setup_2.0.0.zip`
2. Descomprimir archivo `.zip`
3. Ejecutar `Yagua_Setup_2.0.0.exe`
4. Seguir instrucciones de instalacion
5. Ejecutar programa desde el escritorio

### Instalacion (Linux)
1. Descargar `Yagua-2.0.0-x86_64.AppImage`
2. Ejecutar en terminal `chmod +x Yagua-2.0.0-x86_64.AppImage`
3. Luego `./Yagua-2.0.0-x86_64.AppImage`

### Codigo fuente

1. Clona el repositorio.
2. Crea y activa tu entorno virtual.
3. Instala dependencias con `pip install -r requirements.txt`.
4. Ejecuta `python main.py`.

## Requisitos recomendados

- Windows 10/11 o Linux x64
- CPU: 4 nucleos o mas recomendado
- RAM: 8 GB minimo
- Disco: 500 MB libres + espacio para outputs

Dependencias (Linux, segun distro):
- `libfuse2`
- `libgl1`
- `libglib2.0-0`

Limites de carga (segun modulo):
- 100 imagenes por lote (compresion, conversion, resize, rename, LQIP)
- 10 imagenes por lote en Quitar Fondo
- 100 imagenes en limpieza de metadatos (EXIF)

## Uso

1. Abre la app.
2. Selecciona un modulo en la barra lateral.
3. Carga imagenes y procesa.
4. Guarda los resultados en la carpeta de salida.

Nota: Proximamente compatibilidad para macOS.

## Tecnologias Utilizadas

| Tecnologia    | Version | Proposito                         |
| ------------- | ------- | --------------------------------- |
| Python        | 3.13+   | Lenguaje principal                |
| CustomTkinter | 5.2.2   | UI moderna para escritorio        |
| Pillow        | 12.1.1  | Procesamiento de imagenes         |
| pillow-heif   | 0.22.0  | Soporte HEIC/HEIF                 |
| OpenCV        | 4.x     | Procesamiento y previews          |
| EasyOCR       | 1.7.x   | OCR                               |
| rembg         | 2.0.73  | Quitar fondo con IA               |
| piexif        | 1.1.3   | Metadatos EXIF                    |

## Contribucion

- Abre un issue para bugs o ideas.
- Envia un PR con cambios claros y pequenos.
- Mantener el estilo del proyecto y la estructura actual.

## Licencia

MIT License - Ver archivo LICENSE para mas detalles.
