# Estado y pendientes de licencias

Revisión: **2026-10-21**. Este archivo es parte de la distribución y no una
certificación jurídica. Se preservan funciones, motores, formatos y calidad.

## Resuelto técnicamente

- LICENSE de Yagua y el índice de terceros se incluyen explícitamente en los
  recursos de los paquetes Windows y Linux.
- Textos originales disponibles, atribuciones e inventario con versiones y hashes.
- Inter documentada mediante su nombre/copyright/licencia embebidos y una copia
  separada del texto OFL del proyecto. Noto mantiene sus originales y procedencia.
- Los avisos situados fuera de metadatos se recogen conservando su ruta de origen;
  versiones equivocadas y archivos ausentes o alterados hacen fallar el check.
- Inventario reproducible de binarios nativos de cada paquete, incluyendo los no
  clasificados, sin eliminar DLL/SO ni afirmar que todos usan la licencia de Python.

## Requiere revisión jurídica antes de afirmar cumplimiento integral

Actualización técnica: se incluyen cinco distribuciones fuente originales de
PyPI, verificadas contra las versiones usadas y sus hashes. Ver `SOURCE_CODE.md`.
También se incluyen fuentes upstream de las versiones nativas detectadas en
Windows: libheif 1.21.2, libde265 1.0.16, GEOS 3.13.1 y x265 4.1+1-1d117be.
Se fijaron commits y hashes; falta verificar parches/recetas de los wheels y
los builds Linux. Los avisos genéricos de pillow-heif no coinciden con todas
las versiones nativas observadas y no sustituyen esa comprobación.
Para certifi/tqdm quedan proporcionadas esas fuentes y avisos de acceso; esto no
certifica componentes nativos ni equivalencia de todos los wheels con los sdists.
Las acciones de la tabla que consisten en identificar builds, reunir materiales
y comprobar el empaquetado son trabajo técnico; no requieren por sí mismas
contratar un abogado. Los posibles conflictos de licencias requieren resolver
la interpretación o conseguir permisos antes de declararlos cerrados.

| Tema | Evidencia | Acción concreta pendiente |
| --- | --- | --- |
| HEIC: pillow-heif, libheif, libde265, x265 | LICENSES_bundled del wheel 1.3.0 declara GPLv2/LGPLv3; incluye URLs a fuentes. Los números declarados en ese aviso no certifican la versión efectiva de cada DLL/SO. | Determinar las versiones/binarios reales y condiciones del conjunto; obtener fuentes correspondientes, parches y scripts de compilación/instalación que exijan sus licencias; definir una vía válida de entrega. No relicenciar Yagua automáticamente. |
| GEOS, python-bidi y FFmpeg cuando esté incluido | Textos LGPL incluidos o referenciados por los wheels; inventario nativo por build. | Verificar versiones, configuración de compilación, fuentes correspondientes y posibilidad de sustituir/revincular las bibliotecas según la licencia aplicable. Revisar el efecto del congelado sobre los módulos Python LGPL. |
| certifi y tqdm | Textos MPL/MIT originales y sdists de las versiones exactas incluidos, sin parches de Yagua; aviso de acceso en SOURCE_CODE.md. | Verificar que futuras actualizaciones mantengan fuentes y avisos; si cambian archivos cubiertos, registrar y entregar las modificaciones. |
| TBB/tcmlib Windows | Intel Simplified Software License de los wheels: redistribución binaria con condiciones, restricciones de modificación/ingeniería inversa. | Revisar compatibilidad con los componentes copyleft distribuidos y límites de redistribución. No describir estos binarios como MIT o completamente open source. |
| Codecs y patentes | HEVC/HEIC y otros codecs tienen condiciones técnicas y licencias de implementación propias. | Evaluar aparte el alcance de patentes según territorios y distribución; una licencia open source no prueba por sí sola ausencia de patentes. |

No se ha preparado una oferta escrita de fuentes: una promesa sin los materiales
comprobados no subsana las obligaciones. Un enlace genérico al proyecto upstream
o el ZIP de fuentes de Yagua tampoco reemplaza las fuentes correspondientes de
sus componentes. La interpretación del conjunto requiere un profesional con
experiencia en distribución de software libre.

## Procedencias pendientes

- **Modelos:** los cinco archivos y sus hashes observados en carpetas temporales
  están registrados; se conservan licencias de los proyectos de origen. Falta
  confirmar el alcance específico de la autorización para los pesos publicados
  y las conversiones ONNX. No se equiparan automáticamente pesos y código.
- **Iconos:** el responsable declaró Material Symbols/Icons de Google. Su licencia
  Apache 2.0 está incluida, pero cada PNG sin correspondencia exacta con el
  original permanece pendiente. `github.png` representa una marca de tercero y
  no se declara Material por su apariencia. No se sustituye ningún icono.
- **Logo:** procedencia declarada Gemini; conservar conversación/archivo original
  y modificaciones humanas si existen. No se certifica copyright exclusivo ni
  disponibilidad registral del nombre. La elección «Yagua» no se cambia.
- **Binarios Linux y componentes anidados:** revisar el informe del paquete real,
  los avisos capturados de sus wheels, los copyright de paquetes del sistema y
  cualquier binario no clasificado. Los metadatos del paquete principal no
  certifican todos los componentes incluidos.

## Fuentes de consulta

- [pillow-heif 1.3.0: licencias de binarios](https://raw.githubusercontent.com/bigcat88/pillow_heif/v1.3.0/LICENSES_bundled.txt)
- [GNU: redistribución de binarios y fuentes](https://www.gnu.org/licenses/gpl-faq.en.html#UnchangedJustBinary)
- [GNU: distribución y enlace con bibliotecas LGPL](https://www.gnu.org/licenses/gpl-faq.en.html#LGPLStaticVsDynamic)
- [Google Material Icons](https://github.com/google/material-design-icons/blob/master/LICENSE)
- [OFL oficial](https://openfontlicense.org/open-font-license-official-text/)
- [Excepción de PyInstaller](https://pyinstaller.org/en/stable/license.html)
- [Google: contenido generado](https://policies.google.com/terms?hl=es)

## Qué no se hizo

No se cambiaron licencias del código de Yagua, dependencias ni procesamiento.
No se publicó una versión, no se firmaron ofertas de fuentes y no se registró
ninguna marca ni software. No se alteró la web ni se afirmó riesgo jurídico cero.
