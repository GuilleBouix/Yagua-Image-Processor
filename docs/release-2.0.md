# Preparación de Yagua 2.0

Estado: en preparación, sin autorización de publicación.

## Versión y base

- Nombre público: Yagua 2.0. Versión técnica: 2.0.0.
- Rama de trabajo: main.
- Commit inicial: `35153eee09565421ac4fffe61bcde282bf898087`.
- Inventario inicial local: `audit/release-2.0-stage1/baseline.json`. Registra los
  tags remotos, las releases, sus identificadores y los nombres, tamaños, hashes
  publicados y URLs de sus archivos. No es una copia descargada de los binarios.
- En el inventario del 25 de octubre: 16 tags, 13 releases públicas y 61 archivos
  adjuntos. Nueve releases son preliminares 2.0.1-rc y cuatro son estables 1.x.
- El tag `win-v2.0.1-rc.7` existe, pero no aparece una release correspondiente
  en el listado consultado. La lista final se volverá a comprobar antes de lanzar.

## Actualizaciones

El actualizador de 2.0.0 consulta
`GuilleBouix/Yagua-Image-Processor`. Conserva la configuración opcional de
repositorio y plataforma utilizada para forks y pruebas.

Sólo ofrece versiones estables superiores de la misma plataforma, con prefijos
`win-v` y `linux-v`. Descarta borradores, releases marcadas como preliminares y
tags de versiones preliminares o de desarrollo aunque GitHub los marque estables.
Los fallos de conexión o de respuesta siguen distinguiéndose de no encontrar
actualizaciones.

### Migración desde 2.0.1-rc

Para pasar de una RC 2.0.1 a 2.0.0 hay que descargar el paquete estable de la
plataforma e instalarlo manualmente una vez. En Windows se utilizará el
instalador; para portable y AppImage se sustituirá el paquete de la aplicación.
Los archivos personales no forman parte del paquete.

2.0.0 es inferior a 2.0.1-rc para el comparador de versiones. Cambiar las RC
publicadas a borradores no altera ese comportamiento en las aplicaciones ya
instaladas. No se añade una excepción que simule una actualización superior.
La conservación de preferencias al sustituir la RC se comprobará con los
paquetes finales en la etapa de aceptación.

## Control por etapas

Cada etapa requiere revisión y aprobación antes de comenzar la siguiente.

| Etapa | Estado |
| --- | --- |
| 1. Versión, inventario y política de actualización | Comprobada y aprobada |
| 2. Estabilización y validación completa en Windows y Ubuntu | Comprobada; pendiente de aprobación para avanzar |
| 3. Paquetes candidatos y requisitos de distribución | En preparación y validación |
| 4. Aceptación en Windows 11 y Ubuntu 22.04 con escritorio limpios | Pendiente |
| 5. Notas finales, web y releases en borrador | Pendiente |
| 6. Publicación y comprobación pública | Pendiente de aprobación explícita |

La etapa 1 pasó 62 pruebas dirigidas en Windows y 62 en Ubuntu con Python 3.13,
incluidos los estados de la pestaña Actualizaciones y el aviso de inicio.
Los resultados locales están en `audit/release-2.0-stage1/`. No sustituyen la
suite completa, las pruebas de paquetes ni la aceptación de las etapas siguientes.

### Resultado de la etapa 2

- Python 3.13.13: 794 pruebas aprobadas en Windows 11 y 794 en Ubuntu
  26.04.1 mediante WSL/Xvfb. Cada suite emitió cinco avisos de Pillow sobre EXIF.
- Metadatos: diez repeticiones de cada combinación de 1360×720/900×600 y
  escalas 100/75/50 %, 60 casos aprobados por sistema, recorriendo las tres
  pestañas con el lector real y exigiendo la foto renderizada.
- La corrección afecta al aislamiento y sincronización de las pruebas:
  entrega asíncrona, finalización de recursos Tk en el hilo principal y búsqueda
  predeterminada de pytest limitada a `tests/`. No cambia el procesamiento.
- Ruff y Pyright aprobados en ambos entornos; dependencias compatibles y
  comprobación del diff sin errores.
- Matriz visual de los módulos, pestañas, estados vacíos/cargados y scroll en
  ambos tamaños y escalas, sin errores registrados. Se inspeccionaron capturas
  representativas. OCR y Quitar Fondo se probaron con modelos reales en caché,
  red bloqueada, guardado/exportación y limpieza/recarga en ambos sistemas.
- Evidencia local: `audit/release-2.0-stage2/report.md`, logs y capturas.
  La reproducción y sus límites están en `reproduction.md` del mismo directorio.

Estos resultados corresponden a la app ejecutada desde el código fuente.
No validan todavía instaladores, portable ni AppImage, ni sustituyen la
aceptación en máquinas limpias de Windows 11 y Ubuntu 22.04 de la etapa 4.
Al cerrar la etapa 2 no se habían hecho commits, push, tags, compilaciones ni
cambios en releases. Para la etapa 3 se autorizó commit y push exclusivamente
para compilar y validar candidatos, sin tags ni publicación.

### Preparación de la etapa 3

`candidates.yml` construye Windows y Linux desde el mismo commit mediante los
workflows reutilizables `build-windows.yml` y `build-linux.yml`, sin permisos
de escritura en el repositorio. Los ejecutables, hashes e informes permanecen
como artefactos de Actions durante 30 días. No son releases ni descargas de la
web; el acceso a estos artefactos sigue las reglas del repositorio en GitHub.

Los workflows `release.yml` y `release-linux.yml` quedan separados: sólo se
inician manualmente y reciben una versión, un commit y el identificador de una
ejecución candidata. Comprueban procedencia y hashes antes de usar los archivos
ya construidos. No compilan ni se ejecutan al crear un tag.

La publicación de estos candidatos sigue pendiente de las etapas de aceptación
y de aprobación explícita. La existencia de un artefacto validado técnicamente
no cierra por sí sola los pendientes de `legal/REVIEW.md`.

## Releases anteriores

Durante la preparación se mantienen intactas todas las releases y tags.
En el lanzamiento, tras verificar la lista exacta, las releases 2.0.1-rc
acordadas se pasarán a borradores conservando archivos y tags. No se eliminarán.
Las estables 1.x se conservarán como históricas.

Los tags finales serán `win-v2.0.0` y `linux-v2.0.0`, sobre el mismo commit
validado. Todavía no deben crearse ni iniciarse los workflows de publicación;
durante la etapa 3 sólo se ejecutan los de construcción y validación.
