<img width="1761" height="497" alt="banner" src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" />

# Yagua - Procesador de Imágenes

Aplicación de escritorio para procesar imágenes en lote de forma rápida y elegante. Pensada para flujos de trabajo reales: compresión, conversión, quitar fondo con IA, metadatos EXIF y LQIP/Base64.

<a href="https://www.paypal.com/paypalme/guillebouix?locale.x=es_XC&country.x=AR" target="_blank"><img width="300" alt="paypal_donate_button" src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" />
</a>

## 📖 Descripción

Yagua surgió como alternativa a las herramientas web de procesamiento de imágenes: limitadas y con planes de pago para tareas que deberían ser simples. Es una app de escritorio gratuita y open source que corre todo localmente.

Está pensada para desarrolladores web, diseñadores, fotógrafos y cualquier usuario que necesite procesar imágenes en lote sin depender de un navegador ni pagar una suscripción.

Yagua integra en una sola interfaz features orientadas al flujo de trabajo web moderno: generación de LQIP y Base64, quitar fondo con IA (rembg, funciona offline una vez descargado el modelo), edición de metadatos EXIF y compresión/conversión en lote sin límite de archivos.

## ✨ Features

- Compresión inteligente con control de calidad
- Conversión entre múltiples formatos de imagen
- Eliminación de fondo con IA (rembg)
- Redimensionado, recorte y edición en canvas
- Extracción automática de paleta de colores
- Renombrado masivo con vista previa
- Gestión de metadatos EXIF (visualizar, editar y limpiar)
- Generación de LQIP y codificación Base64
- Soporte multi-idioma (ES / EN / PT)
- Temas oscuros predefinidos

## 🖼️ Galería

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

## ⚙️ Instalación

### 🖥️ Instalación (Windows)
1. Descargar `Yagua_Setup_1.X.X.zip`
2. Descomprimir archivo `.zip`
3. Ejecutar `Yagua_Setup_1.X.X.exe`
4. Seguir instrucciones de instalación
5. Ejecutar programa desde el escritorio

### 🐧 Instalación (Linux)
1. Descargar `Yagua-1.X.X-x86_64.AppImage`
2. Ejecutar en terminal `chmod +x Yagua-1.X.X-x86_64.AppImage`
3. Luego `./Yagua-1.X.X-x86_64.AppImage`

### 🐍 Código fuente

1. Clona el repositorio.
2. Crea y activa tu entorno virtual.
3. Instala dependencias con `pip install -r requirements.txt`.
4. Ejecuta `python main.py`.

## 🧩 Requisitos recomendados

Para que Yagua funcione de manera fluida, especialmente con lotes grandes (hasta 100 imágenes):

#### ✅ Sistema
- Windows 10/11 o Linux x64
- CPU: 4 núcleos o más recomendado
- RAM: 8 GB mínimo
- Disco: 500 MB libres + espacio para outputs
#### ✅ Dependencias (Linux)
- AppImage suele correr directo, pero puede requerir:
  - `libfuse2`
  - `libgl1`
  - `libglib2.0-0`
#### ✅ Límites de carga
- 100 imágenes por lote (compresión, conversión, resize, rename, LQIP)
- 10 imágenes por lote en Quitar Fondo
- 100 imágenes en limpieza de metadatos (EXIF)

## 🚀 Uso

1. Abre la app.
2. Selecciona un módulo en la barra lateral.
3. Carga imágenes y procesa.
4. Guarda los resultados en la carpeta de salida.

ℹ️ Nota: Próximamente compatibilidad para macOS.

## 🔧 Tecnologías Utilizadas

| Tecnología        | Versión | Propósito                          |
| ----------------- | ------- | ---------------------------------- |
| Python            | 3.13+   | Lenguaje principal                 |
| CustomTkinter     | 5.2.2   | UI moderna para escritorio         |
| Pillow            | 12.1.1  | Procesamiento de imágenes          |
| piexif            | 1.1.3   | Metadatos EXIF                     |
| rembg             | 2.0.73  | Quitar fondo con IA                |
| Codex             | N/A     | Asistencia de desarrollo           |

## 🤝 Contribución

- Abre un issue para bugs o ideas.
- Envía un PR con cambios claros y pequeños.
- Mantén el estilo del proyecto y la estructura actual.

## ⭐ Apoyá el proyecto

Si Yagua te resultó útil, dejá una estrella en el repo — es gratis y ayuda un montón a que más gente lo encuentre :)

## 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles.
