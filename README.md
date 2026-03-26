<img width="1761" height="497" alt="banner" src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" />

# Yagua - Procesador de Imágenes

Aplicación de escritorio para procesar imágenes en lote de forma rápida y simple. Incluye compresión, conversión, quitar fondo con IA, edición de metadatos y generación de LQIP/Base64.

---

## Tabla de Contenidos

1. [Descripción](#descripcion)
2. [Instalación](#instalacion)
3. [Uso](#uso)
4. [Tecnologías](#tecnologias)
5. [Features](#features)
6. [Contribución](#contribucion)
7. [Créditos](#creditos)
8. [Licencia](#licencia)

---

## Descripción

Yagua surgió como alternativa a las herramientas web de procesamiento de imágenes: lentas, con límites de archivos, y con planes de pago para tareas que deberían ser simples. Es una app de escritorio gratuita y open source que corre todo localmente.

Está pensada para desarrolladores web, diseñadores, fotógrafos y cualquier usuario que necesite procesar imágenes en lote sin depender de un navegador ni pagar una suscripción.

A diferencia de tools como IrfanView o XnConvert, Yagua integra en una sola interfaz features orientadas al flujo de trabajo web moderno: generación de LQIP y Base64, quitar fondo con IA (rembg, funciona offline una vez descargado el modelo), edición de metadatos EXIF y compresión/conversión en lote sin límite de archivos.

---

## Instalación

### Instalador (recomendado)

1. Descarga el instalador de la última release.
2. Descomprime el archivo `.zip`.
3. Ejecuta el `.exe` y sigue el asistente.
4. Abre Yagua desde el escritorio o el menú inicio.

### Desde código (source)

1. Clona el repositorio.
2. Crea y activa tu entorno virtual.
3. Instala dependencias con `pip install -r requirements.txt`.
4. Ejecuta `python main.py`.

---

## Uso

1. Abre la app.
2. Selecciona un módulo en la barra lateral.
3. Carga imágenes y procesa.
4. Guarda los resultados en la carpeta de salida.

---

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.13+ | Lenguaje base |
| CustomTkinter | Interfaz gráfica |
| Pillow | Procesamiento de imágenes |
| piexif | Lectura y edición de metadatos EXIF |
| tkinterdnd2 | Drag & drop |
| rembg | Eliminación de fondo con IA |
| Codex | Asistencia de desarrollo |

---

## Features

- Compresión y conversión de imágenes
- Redimensionar, recortar y canvas
- Renombrado por lotes con preview
- Quitar fondo con IA (rembg)
- Metadatos EXIF (ver, editar, limpiar)
- LQIP / Base64
- Multi-idioma (ES / EN / PT)

---

## Galería

<p align="center">
  <img src="https://github.com/user-attachments/assets/5f4274b6-dec6-434c-82b3-81b8135287a9" width="250"/>
  <img src="https://github.com/user-attachments/assets/a1cbc413-d3e5-4165-a0e6-63a61a4ab012" width="250"/>
  <img src="https://github.com/user-attachments/assets/880d2642-dbb1-41d1-b0da-131f1de007f2" width="250"/>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/7d182d3e-cdf0-4876-868b-ce124b135aeb" width="250"/>
  <img src="https://github.com/user-attachments/assets/7db92616-d5cf-48fd-94fc-d619b3567295" width="250"/>
  <img src="https://github.com/user-attachments/assets/ad0f3d3a-59c9-4644-a0ea-38286e7b316d" width="250"/>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/9117f968-0048-444e-ab9d-a74f7894f45d" width="250"/>
  <img src="https://github.com/user-attachments/assets/7c55eb50-8472-4072-9cd3-b97a905273b7" width="250"/>
  <img src="https://github.com/user-attachments/assets/650b1519-77aa-4c3a-9863-c1a8cb0c9613" width="250"/>
</p>

---

## Contribución

- Abre un issue para bugs o ideas.
- Envía un PR con cambios claros y pequeños.
- Mantén el estilo del proyecto y la estructura actual.

---

## Créditos

Guille Bouix

---

## Licencia

MIT License - Ver archivo LICENSE para más detalles.
