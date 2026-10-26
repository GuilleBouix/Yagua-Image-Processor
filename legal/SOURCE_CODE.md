# Código fuente de componentes incluidos

Actualización 2026-10-26: [`distribution/README.md`](distribution/README.md)
documenta las fuentes/parches Ubuntu y recetas adicionales reunidas para los
candidatos Windows/Linux. `scripts/ci/source_materials.py` prepara un archivo
separado con hashes verificados. Es material de revisión, todavía no una
declaración de entrega completa de fuentes correspondientes. Los nueve archivos
descritos a continuación continúan incluidos dentro de la aplicación.

Las fuentes originales publicadas para estas versiones se incluyen sin modificar
en `legal/sources/`. No hace falta internet para obtener estas copias:

| Componente | Versión | Archivo |
| --- | --- | --- |
| certifi | 2026.2.25 | `sources/certifi-2026.2.25.tar.gz` |
| tqdm | 4.67.3 | `sources/tqdm-4.67.3.tar.gz` |
| python-bidi | 0.6.7 | `sources/python_bidi-0.6.7.tar.gz` |
| Shapely | 2.1.2 | `sources/shapely-2.1.2.tar.gz` |
| pillow-heif | 1.3.0 | `sources/pillow_heif-1.3.0.tar.gz` |

`sources/manifest.json` identifica URL oficial de PyPI, versión, tamaño y SHA256.
Los hashes se contrastaron con los metadatos de PyPI al descargar. Las licencias
originales se conservan dentro de los archivos y en `licenses/`.
Estas fuentes mantienen sus licencias propias, incluida MPL para certifi y las
partes correspondientes de tqdm; MIT de Yagua no las reemplaza.

En el instalador y portable Windows esta carpeta está dentro de `_internal/legal/`;
en el AppImage, dentro de `usr/lib/yagua/_internal/legal/` tras su extracción.

## Alcance comprobado

También se incluyen fuentes upstream de libheif **1.21.2**, libde265 **1.0.16**
y GEOS **3.13.1**, con commits completos, URLs y hashes en el mismo manifiesto.
Las versiones se consultaron mediante `pillow_heif.libheif_info()` y
`shapely.geos_version_string` en el entorno aislado del build Windows.
Los avisos genéricos de pillow-heif mencionan versiones anteriores: no se usan
para atribuir una versión al binario real. Los archivos de estas tres fuentes
son snapshots de los tags upstream, no reconstrucciones de los wheels.

x265 informa **4.1+1-1d117be**. Se incluye la fuente de la revisión
**1d117bed4747758b51bd2c124d738527e30392cb**, resuelta mediante la API del
repositorio oficial de Multicoreware y descargada desde ese repositorio.
Las recetas publicadas de pillow-heif y sus dos parches de CMake para x265 se
reunieron en el material adicional, fijado por commit. No basta el tag 3.4 que
aparece en el aviso genérico. No se reconstruyó el wheel ni se resolvieron todas
las dependencias externas variables de esas recetas. Las mismas versiones
nativas se consultaron también en Linux durante la revisión de candidatos;
el detalle y sus límites están en `distribution/README.md`.

Se distribuyen los archivos fuente publicados de las cinco versiones indicadas.
Yagua no aplica parches a esas fuentes. Esto no significa que se haya reproducido
la compilación de sus wheels ni verificado su equivalencia binaria.

Los archivos fuente reunidos no se presentan como entrega completa de las
fuentes de GEOS, libheif, libde265 o x265 incluidos en los wheels. Esas bibliotecas
requieren identificar el build real, fuentes, parches y scripts correspondientes.
También queda abierta la comprobación de sustitución/reenlace de componentes LGPL
en el ejecutable congelado. Ver `REVIEW.md`.

No se emite una oferta escrita de entrega futura: estas nueve copias se entregan
directamente. No se promete que el código de Yagua por sí solo cubra el de terceros.

Referencias: [MPL, distribución de bibliotecas](https://www.mozilla.org/en-US/MPL/2.0/FAQ/),
[licencias nativas declaradas por pillow-heif 1.3.0](https://raw.githubusercontent.com/bigcat88/pillow_heif/v1.3.0/LICENSES_bundled.txt).
