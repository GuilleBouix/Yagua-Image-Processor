# Yagua — avisos de terceros / third-party notices

Revisión técnica: 2026-10-21. El código original de Yagua conserva la licencia
[MIT](LICENSE), Copyright (c) 2026 Guillermo Daniel Bouix. Esa licencia no cambia
las condiciones de las bibliotecas, modelos, fuentes, iconos o runtimes incluidos.

**No se declara que el paquete completo sea MIT ni que esta revisión certifique
su cumplimiento jurídico.** Hay obligaciones abiertas en [legal/REVIEW.md](legal/REVIEW.md).
English: Yagua's original code is MIT-licensed. Bundled components retain their own
terms. This notice inventory is not legal clearance; open obligations are documented
in `legal/REVIEW.md`.

## Inventario y textos originales

- [Inventario de versiones, procedencias, hashes y estados](legal/inventory.json).
- [Guía de comprobación y mantenimiento](legal/README.md).
- [Fuentes originales incluidas y su alcance](legal/SOURCE_CODE.md): cinco
  distribuciones fuente, con versiones, URLs y hashes comprobados.
- `legal/licenses/wheels/`: textos originales de los wheels revisados, con sus
  avisos nativos y de terceros. Se conservan completos, sin traducir ni reemplazar
  los términos originales por un resumen.
- `legal/licenses/upstream/`: originales adicionales obtenidos de sus autores,
  incluidos Inter, Material Icons, Python y los proyectos de modelos.
- En cada build, `legal/installed-notices/` conserva los avisos del entorno de
  construcción de esa plataforma, también los situados fuera de `.dist-info`.
  `legal/installed-inventory.json` registra versiones y hashes de esos archivos.
- Las Noto Sans CJK JP/SC originales y su OFL 1.1 permanecen en
  `assets/fonts/noto-cjk/`, con revisión y SHA256 fijados.

## Atribuciones principales

- CustomTkinter: Tom Schimansky; MIT según el texto LICENSE distribuido. Su campo
  de metadatos menciona CC0; no se utiliza ese campo como prueba única de licencia.
- Pillow, NumPy, SciPy, PyTorch, Torchvision, ONNX Runtime, rembg, PyMatting,
  OpenCV, EasyOCR y el resto de los componentes mantienen los titulares y términos
  de sus textos originales, enumerados por distribución en el inventario.
- Inter: The Inter Project Authors; SIL Open Font License 1.1. Archivo original
  local identificado como versión 4.001; copyright y URL de licencia embebidos.
- Noto Sans CJK: autores indicados en las fuentes y el texto OFL original incluido.
- Google Material Symbols / Material Icons: Google; Apache License 2.0 para los
  recursos que correspondan a esa colección. El autor de Yagua declaró esa
  procedencia; los PNG sin correspondencia individual comprobada están marcados
  como pendientes. No se atribuye automáticamente a Google cada imagen del proyecto.

## Modelos descargados en el primer uso

CRAFT, los reconocedores inglés/latino de EasyOCR, ISNet y U2NetP se identifican
por nombre de archivo, proveedor, URL de descarga y SHA256 observado en modelos
temporales de validación. No se añaden pesos a la instalación ni se descargan
modelos al consultar estos documentos. La licencia de un repositorio de código
no se presenta por sí sola como autorización independiente de sus pesos.

## Componentes con condiciones particulares

HEIC incluye bibliotecas GPL/LGPL; Shapely incluye GEOS LGPL; python-bidi utiliza
LGPL; certifi y partes de tqdm tienen condiciones MPL. FFmpeg y otros runtimes
requieren examinar los avisos y la compilación concreta. Los wheels Intel
TBB/tcmlib de Windows tienen términos de redistribución propios.

No se promete una oferta de fuentes de tres años ni se declara cumplida la entrega
de código fuente correspondiente sin disponer y verificar los materiales reales.
Las acciones pendientes están en `legal/REVIEW.md`.

## Identidad visual

Según declaración del responsable del proyecto del 2026-10-21, el logo fue generado
por él con Gemini. «Yagua» abrevia «yaguareté», animal de la fauna de Misiones,
Argentina, lugar donde nació. Se registra esta procedencia; no se afirma que el
resultado de IA tenga derechos exclusivos ni que la marca esté registrada o libre
de conflictos. Los signos de terceros no implican patrocinio ni afiliación.
