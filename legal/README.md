# Recursos legales de la app

Fecha de revisión: **2026-10-21**. Alcance: Windows y Linux, app de escritorio.
La web, los registros de marca, los trámites fiscales y la redacción de privacidad
quedan fuera de esta entrega. No se ha publicado una nueva versión.

## Qué comprueban los checks

1. Presencia y SHA256 de los originales registrados, incluido LICENSE de Yagua.
2. Correspondencia exacta entre las versiones inventariadas y los requirements de
   cada plataforma, incluidas las variantes CPU de Torch y Torchvision en Linux.
3. Inventario y hashes de recursos visuales; un archivo nuevo o cambiado exige
   revisar su procedencia. Un estado pendiente no se convierte en permiso de uso.
4. Durante el build, recogida de avisos de los wheels reales, dentro y fuera de
   `.dist-info`, y comprobación de versión instalada antes de congelar.
5. En el paquete, presencia e integridad de esos avisos y un inventario de DLL,
   PYD, SO y DYLIB con hashes. Las familias nativas son una clasificación orientativa;
   los archivos sin clasificar se enumeran, no se ocultan.

Un resultado `technical_status: passed` significa que esos controles técnicos
pasaron. **`legal_approval` permanece en false**: no es una aprobación de licencias,
patentes, derechos sobre pesos o cumplimiento de GPL/LGPL.

## Comandos offline

Desde la raíz, usando el Python del entorno correspondiente:

```text
python scripts/ci/check_licenses.py
python scripts/ci/check_licenses.py --installed --report build/legal-installed.json
python scripts/ci/check_licenses.py --package dist/Yagua --platform win32 --report build/legal-package.json
python scripts/ci/check_licenses.py --package build/linux-release/package-check/squashfs-root --platform linux --report build/legal-linux.json
```

Los comandos no descargan contenido ni modifican preferencias o imágenes. Los
informes solo se escriben si se solicita `--report`. Las pruebas usan copias
temporales para simular ausencias y corrupción, sin borrar recursos del proyecto.

## Ubicación en los paquetes

PyInstaller 6 coloca los datos en `_internal/`: allí están LICENSE,
THIRD_PARTY_NOTICES.md y `legal/`. En AppImage están bajo
`usr/lib/yagua/_internal/`. El instalador y el portable copian el mismo directorio
de distribución. No se cambia la interfaz ni se incorpora una aceptación de EULA.

## Actualizar dependencias o recursos

`SOURCE_CODE.md` explica las nueve copias fuente incluidas en `sources/`, también
en ambos paquetes. No se descargan durante el uso ni los checks. Su manifiesto
se comprueba contra las versiones de ejecución, hashes y tamaños. Añaden
los archivos fuente comprimidos a la distribución; se mantienen
comprimidos y no se importan durante la ejecución.

- Revisar los textos originales de la versión y wheel nuevos en cada plataforma.
- Actualizar versiones, atribuciones, evidencia, estados y hashes del inventario.
- Conservar el texto original completo y su procedencia; no inferir permisos solo
  del clasificador de PyPI. Un wheel puede incluir licencias adicionales.
- Resolver o trasladar explícitamente los puntos abiertos de REVIEW.md; no
  eliminar un pendiente para hacer pasar el check.
- No editar manualmente `installed-inventory.json`: se genera por build a partir
  de los paquetes instalados. Nunca copiarlo de otro sistema operativo.

El inventario inicial de avisos de wheels se obtuvo del entorno aislado de build
Windows usado en la auditoría, sin instalar ni desinstalar paquetes en VSCode.
Los avisos de los wheels Linux se recogen adicionalmente al construir allí. No se
afirma que el conjunto inicial Windows describa todos los binarios Linux.
