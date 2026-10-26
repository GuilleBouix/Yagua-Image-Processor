# Materiales de distribución de Yagua 2.0

Revisión técnica iniciada el **26 de octubre de 2026**. La candidata privada
validada más reciente se construyó desde `a9ca7f58259f0b60033c6d6e1776d34cf87dbe04`;
sus artefactos incluyen manifiestos propios con commit, árbol, hashes y procedencia.
Los materiales base de este directorio documentan además el trabajo iniciado sobre
`7b0768758c53621a45bfdcc75cea92f237cc3a3f`. Esta revisión no certifica cumplimiento
jurídico integral.

## Material reunido

`materials.json` registra tamaños, SHA-256, procedencias y revisiones. Incluye:

- Las nueve fuentes originales ya distribuidas en `legal/sources/`.
- Las fuentes originales y parches Debian de los 14 paquetes fuente que
  corresponden a los 16 paquetes Ubuntu del `.bundle.yml` real del AppImage.
- Las recetas de pillow-heif 1.3.0, Shapely 2.1.2 y opencv-python 4.13.0.92,
  fijadas por commit, y FFmpeg 8.0.1 usado por el wheel Linux.
- AppRun 2.0.0, AppImageKit 5735cc5 y su submódulo libappimage, con sus avisos
  originales. Los snapshots Git no contienen automáticamente sus submódulos.
- Squashfuse y sanitizers-cmake en las revisiones indicadas por AppImageKit,
  XZ 5.2.3 contrastado con el SHA-512 de la receta y libvpx 1.15.2, cuya versión
  también informa la biblioteca incluida. Se conservan LICENSE y PATENTS.
- Los copyright originales de glibc, gcc-12, libxcrypt y zlib. Los otros
  copyright de paquetes Ubuntu se encontraron en el AppImage candidato.

Los textos GPL 2/3, LGPL 2.1/3 y GFDL 1.3 a los que remiten los copyright
Debian se conservan en `notices/common-licenses/`, copiados de los originales
del sistema Ubuntu. Los nombres de versión se mantienen explícitos.

La cadena Ubuntu se verificó con `gpgv` y el llavero de archivo del sistema:
`InRelease` firmado → SHA-256 de `Sources.gz` → SHA-256 de los 48 archivos.
La huella es `F6ECB3762474EDA9D21B7022871920D1991BC93C`.
El archivo histórico de Jammy identifica las versiones del candidato; no se
presenta como una comprobación de actualizaciones de seguridad actuales.

Los archivos grandes permanecen fuera de Git y de los ejecutables. Para reunirlos
en un archivo separado, sin extraer ni ejecutar código de terceros:

```text
python scripts/ci/source_materials.py --cache RUTA_CACHE --output Yagua-2.0.0-source-materials.tar.xz --download
```

Sin `--download`, sólo se usan las copias locales. Se comprueban todos los hashes
antes de publicar el archivo, y nunca se reemplaza una salida existente. El archivo
incluye el manifiesto. Una firma guardada como evidencia no sustituye repetir la
verificación criptográfica con un llavero confiable si se hace una nueva auditoría.

El workflow de Windows también prepara este archivo como artefacto privado de
Actions y lo vincula al commit y la versión candidata mediante un manifiesto de
hashes. El workflow de Linux añade además el informe de la reconstrucción HEIC.
Estos artefactos sirven para revisión; el manifiesto declara explícitamente que
no son una entrega completa de fuentes correspondientes ni se publican como
releases automáticamente.

## Comprobado en los candidatos

- `tbb12.dll` coincide con el DLL original del wheel Intel 2022.3.1, SHA-256
  `b24e99b40add5ce3132793c10f7325b8e9fdfb4db03465f5103cfb43146a5a9f`.
  No se modificó. Los DLL de tcmlib no aparecen en el paquete Windows.
  `tbbpool` pertenece a Numba; su nombre no le atribuye la licencia Intel.
- El paquete Windows no incluye `opencv_videoio_ffmpeg*.dll`. Que el informe
  de compilación de OpenCV anuncie FFmpeg no demuestra que se distribuya ese DLL.
  El paquete Linux sí incluye bibliotecas FFmpeg LGPL 2.1 o posterior.
- La libc de compatibilidad del AppImage informa `Ubuntu GLIBC 2.35-0ubuntu3`;
  se reunieron la fuente y los parches de esa versión exacta.
- La candidata Linux privada `a9ca7f5` incorpora los avisos AppRun/AppImageKit y
  copyright reunidos. Sus pruebas técnicas pasaron. La aprobación legal sigue
  marcada como pendiente en los informes de ambas plataformas.

## Iconos

El autor confirmó que descargó los PNG de Google Material Icons/Symbols.
Se registra esa procedencia declarada y se conserva Apache 2.0; no se afirma
una comparación independiente de cada PNG con un SVG original. No hace falta
recrear los archivos para registrar esa declaración. Los hashes no cambian.

`github.png` se trata por separado como marca de GitHub. Su uso actual enlaza al
repositorio del proyecto, uno de los usos contemplados por las
[directrices de GitHub](https://brand.github.com/foundations/logo).
No se atribuye Apache 2.0 a esa marca ni se afirma patrocinio de GitHub.

## Pendientes concretos

El detalle de las bibliotecas nativas y la diferencia entre el AppImage anterior
y la candidata Linux actual está en [`NATIVE_COMPONENTS.md`](NATIVE_COMPONENTS.md).

1. **Pesos ISNet:** `isnet-general-use.onnx` se descarga desde la publicación de
   modelos de rembg y procede del modelo general de DIS. DIS limita Apache 2.0
   explícitamente al código y a la métrica; no encontramos una licencia expresa
   para esos pesos. La consulta oficial sobre los pesos sigue abierta, sin una
   respuesta del autor al revisar este informe. No se trasladan al modelo los
   términos del dataset.
2. **Pesos U2Net:** `u2netp.onnx` se descarga de la publicación de modelos de
   rembg. Su mantenedor aclara que MIT cubre el código de rembg, no los modelos;
   señala que los derechos de U2Net corresponden a su upstream Apache-2.0. A la
   vez, declara que no puede reconstruir el checkpoint exacto ni el proceso que
   produjo el ONNX publicado por rembg. La licencia upstream es favorable, pero
   la cadena de conversión del archivo usado no está verificada.
3. **Pesos OCR:** `craft_mlt_25k.pth`, `english_g2.pth` y `latin_g2.pth` se
   descargan de las publicaciones oficiales de EasyOCR. EasyOCR licencia su
   código bajo Apache-2.0 y atribuye CRAFT a Clova; el repositorio oficial de
   CRAFT ofrece su código bajo MIT y enlaza los pesos por separado. No hallamos
   una licencia específica para cada uno de estos archivos de pesos. No
   atribuimos automáticamente a los pesos la licencia del código.
4. **Fuentes correspondientes:** la candidata Linux `a9ca7f5` ya reconstruye
   HEIC desde fuentes fijadas y pasó las pruebas del AppImage. El `libmvec` del
   wheel anterior fue sustituido por `libmvec.so.1` de Ubuntu GLIBC 2.35, cuya
   fuente se reunió. Aún falta revisar la clasificación/licencia de los binarios,
   cerrar dependencias externas variables de algunas recetas y comprobar la
   sustitución o el reenlace de LGPL en la distribución congelada.
5. **Conjunto distribuido:** Intel permite redistribuir sus binarios sin
   modificar bajo sus condiciones. Queda revisar su combinación concreta con
   los componentes copyleft, en lugar de afirmar que es Apache/MIT o prohibir
   automáticamente todo TBB. Las cuestiones territoriales de patentes de
   codecs tampoco se resuelven comprobando hashes.

Referencias de primera mano para los pesos: [términos de DIS](https://github.com/xuebinqin/DIS#term-of-use),
[consulta de permisos ISNet](https://github.com/xuebinqin/DIS/issues/150),
[aclaración del mantenedor de rembg sobre modelos](https://github.com/danielgatis/rembg/issues/837),
[configuración de URLs de EasyOCR](https://github.com/JaidedAI/EasyOCR/blob/master/easyocr/config.py),
[atribución de CRAFT en EasyOCR](https://github.com/JaidedAI/EasyOCR#acknowledgement-and-references) y
[licencia/repositorio de CRAFT](https://github.com/clovaai/CRAFT-pytorch).

La entrega se identifica como **materiales de revisión**, no como oferta
escrita ni como fuentes correspondientes completas. No se publica una estable
ni se pasa a la etapa de aceptación por el solo hecho de generar este archivo.
