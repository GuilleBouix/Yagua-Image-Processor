# Componentes nativos: revisión del 26 de octubre de 2026

Paquetes candidatos del commit `7b0768758c53621a45bfdcc75cea92f237cc3a3f`.
No se alteraron los paquetes, las dependencias ni los modelos durante esta revisión.

## Qué se comprobó

| Componente | Evidencia del candidato | Material reunido |
| --- | --- | --- |
| Runtime AppImage | Identifica 5735cc5; su ELF necesita libdl, libpthread, libz y libc. | AppImageKit y libappimage fijados por commit; cabecera MIT original de runtime.c, incluyendo sus dos atribuciones. |
| Squashfuse del runtime | La receta de libappimage fija 1f98030 y conserva el script de parches. | Snapshot de la revisión completa, licencia BSD y aviso específico de fuseprivate.c. No se atribuye LGPL a ese archivo por contener «fuse» en su nombre. |
| XZ del runtime | La receta fija 5.2.3 y SHA-512 del archivo original. | Archivo fuente completo, incluyendo configure, contrastado con ese SHA-512. COPYING declara liblzma de dominio público; las herramientas y archivos de construcción tienen condiciones propias. |
| FFmpeg Linux | av_version_info informa 8.0.1; las cinco bibliotecas consultadas informan LGPL 2.1 o posterior; avcodec/avformat exponen su configuración de compilación. | Archivo fuente 8.0.1 y receta de opencv-python fijada por commit. No se deduce la licencia únicamente de requirements.txt. |
| libvpx de FFmpeg | vpx_codec_version_str informa v1.15.2. | Revisión completa del tag oficial, LICENSE y PATENTS originales. |
| OpenSSL de FFmpeg | OpenSSL_version informa 1.1.1k FIPS, aunque la receta publicada menciona 1.1.1w. | El wheel ya incluye los textos OpenSSL/SSLeay. Se registra la diferencia; no se afirma que la receta de 1.1.1w reproduzca ese binario ni que el nombre FIPS certifique el paquete. |
| GEOS / libde265 | Las API separadas informan GEOS 3.13.1-CAPI-1.19.2 y libde265 1.0.16. | Fuentes ya reunidas y recetas de los wrappers fijadas por commit. |
| liblzma de Pillow | La API informa 5.8.2. | Se distingue de XZ 5.2.3 del runtime. No se usa la fuente de una versión como prueba de la otra. |

La evidencia con rutas, SHA-256, dependencias ELF y respuestas de API está en
`evidence/native-linkage.json`. La consulta se hizo con ctypes desde el Python
del sistema WSL, fuera de AppRun; no sustituye una prueba de la aplicación.
La carga directa de libheif en ese contexto no resolvió la ruta de libmvec que
AppRun prepara. Se conserva ese resultado sin presentarlo como un fallo nuevo de
Yagua: los candidatos ya aprobaron las verificaciones reales de HEIC y arranque.

## Hueco del AppImage anterior y reemplazo en validación

El AppImage anterior incluía esta biblioteca procedente del wheel:

```text
runtime/compat/usr/lib/yagua/_internal/pillow_heif.libs/libmvec-2-583a17db.28.so
```

Su revisión de distribución exacta no se pudo identificar con las recetas
reunidas. Las fuentes Ubuntu glibc 2.35 entregadas para la libc de compatibilidad
no prueban que correspondan a esta biblioteca de la serie 2.28. No se rellena
ese dato suponiendo una revisión de CentOS/RHEL por el nombre del archivo.

El responsable autorizó recompilar la cadena el 26 de octubre. `scripts/ci/build_heic_linux.py` reconstruye
libheif 1.21.2, libde265 1.0.16 y x265 de la misma revisión desde las fuentes
verificadas, con los dos parches publicados de pillow-heif y el include de
cstdint que necesita json11 con GCC 15. Se genera explícitamente el archivo de
versión de x265 porque el snapshot original contiene datos antiguos. NUMA se
desactiva explícitamente para mantener estable la lista de dependencias.

El wrapper Python conserva pillow-heif 1.3.0. Únicamente se ajusta su enlace ELF
a la cadena reconstruida; el informe registra hashes antes y después y conserva
los originales en el directorio de construcción. La cadena compilada pasó las
pruebas locales de nueve formatos y codificación/decodificación HEIC de 10 y
12 bits. El build oficial para la base Linux objetivo y la validación del
AppImage candidato siguen pendientes.

La sustitución de bibliotecas LGPL modificadas y la revisión del conjunto con
los términos Intel siguen pendientes. Cargar una biblioteca original por su ruta
separada no demuestra por sí solo que se haya probado una versión modificada.
