# Validación local: Recortar, Canvas y Paleta por lotes

Código fuente de `main`, sobre el commit base `19889cf`, con los cambios locales
sin commitear. No se generaron paquetes, tags ni releases.

## Entornos

| Sistema | Python | Interfaz |
|---|---|---|
| Windows 11 x64, 10.0.26200 | 3.13.13 | Tk 8.6, CustomTkinter 5.2.2 |
| Ubuntu 26.04.1 LTS x64, WSL2 | 3.13.17 | Xvfb, Tk 8.6, CustomTkinter 5.2.2 |

Pillow 12.1.1 y las dependencias fijadas del proyecto. El entorno completo Linux
incluye las dependencias de IA y el encoder HEIF; no se usaron stubs para aprobar
el tipado. Las pruebas emplean preferencias temporales y el bloqueo de HTTP de
`scripts/verify.py`. Las pruebas unitarias que simulan IA no demuestran por sí
solas la descarga ni la calidad de modelos dentro de paquetes compilados.

## Alcance comprobado

- Recorte centrado exacto, proporciones anteriores, orientación EXIF, valores
  inválidos y omisión de imágenes pequeñas sin detener el lote. Sliders y
  dimensiones originales, cambios de selección y conservación de controles.
- Canvas con colores y transparencia, cancelación del selector, píxeles
  semitransparentes, preview frente a salida real y formatos mezclados. Conversión
  a PNG cuando corresponde, conservación del original y confirmación cancelada.
- Guardado real de lotes de 1 y 100 en Recortar, Canvas y Paleta. Copias y
  sobrescritura en Canvas; exportaciones sin reemplazo y nombres repetidos en
  Paleta. Fallos parciales, fuentes protegidas y publicación atómica.
- Paleta con cargas sucesivas, duplicados, exceso del límite, selección rápida,
  limpieza, caché por cantidad y revisión del archivo, colores transparentes,
  archivos ilegibles y resultados tardíos. Muestras a todo el ancho al cambiar
  entre 4/6/8/10/12 colores, incluyendo volver de 12 a 4.
- Ventanas grandes y 900×600, escalas 100/75/50%; matriz de idiomas y temas.
  Las comprobaciones automáticas de geometría no sustituyen la revisión visual
  manual del usuario.

## Xvfb y estabilidad de las pruebas

El fallo `X Error: BadAlloc` se reprodujo antes del cambio. La lista virtual
todavía solicitaba una ventana física del alto del lote (más de 36.000 píxeles
para 500 filas). Ahora conserva el rango lógico de scroll y desplaza una ventana
pequeña con las filas visibles. Se conservan las aserciones originales y se
comprueban 500 y 5.000 filas, selección, reutilización y desplazamiento al final
y de vuelta al inicio. Los callbacks se cancelan antes de destruir la lista.

Se detectó y corrigió un corte de Paleta al 50%: la muestra usaba un canvas
nativo con alto fijo y el último botón quedaba fuera del espacio reservado.
Ahora usa una muestra CTk escalable. Las 21 pruebas relacionadas aprobaron en
ambos sistemas después del ajuste, incluyendo todos los números de colores.

La matriz de construcción limpia el frame y su contenedor exterior, en ese
orden. CTk no elimina ese contenedor al destruir sólo el frame. Las ventanas de
prueba se ocultan antes de cerrar y en Windows se colocan fuera del escritorio:
conservan tamaños y visibilidad de Tk, sin recibir clics accidentales del usuario.
Las primeras corridas de diagnóstico de Windows no se consideran aprobadas;
los resultados finales se registran separadamente.

## CI

Se adelantan sintaxis y comprobaciones de las vistas sensibles, sin eliminar
pruebas ni repetir una aserción hasta que pase. Las particiones deben cubrir
exactamente la suite completa. Se conservan informes de ambos grupos y el JUnit
conjunto; un fallo impide aprobar el checkpoint. Ver [recuperación de CI](CI_RECOVERY.md).

Ruff, Pyright, sintaxis Python, lectura YAML de los diez workflows, particiones,
preflight de ambas plataformas y `git diff --check` forman parte de esta ronda.

## Resultados

La suite completa Ubuntu aprobó 1.060 pruebas. Las cuatro pruebas adicionales de
Canvas con lotes reales también aprobaron; la matriz con su limpieza actual
aprobó sus 27 casos. Los cinco avisos de Pillow corresponden a EXIF deliberadamente
dañado en las pruebas de lectura, no a errores ocultados.

El informe conjunto Ubuntu contiene 1.064 casos distintos, sin omisiones,
fallos ni errores. Se comprobó que las cuatro pruebas adicionales no estuvieran
duplicadas en el primer informe.

| Sistema | Lógica y servicios | Interfaz | Resultado conjunto |
|---|---:|---:|---|
| Windows | 579 aprobadas, 1 omitida | 484 aprobadas | 1.063 aprobadas, 1 omitida |
| Ubuntu | Suite completa y casos adicionales | Incluida | 1.064 aprobadas |

La omisión Windows comprueba permisos de ejecución y enlaces simbólicos POSIX;
esa prueba sí se ejecutó en Ubuntu. No hubo pruebas fallidas ni errores en los
informes conjuntos finales. Las 21 comprobaciones específicas de Paleta y listas
se volvieron a ejecutar después del ajuste de altura al 50%, aprobadas en ambos
sistemas.

La partición UI Windows completa tardó 25 min 46 s en esta máquina; la suite
Ubuntu completa tardó 13 min 56 s. Son tiempos locales, no predicciones para
Actions. La matriz exhaustiva sigue siendo costosa: el orden prioritario detecta
antes problemas de las vistas sensibles, sin reducir su cobertura.

Los XML conjuntos y los diagnósticos locales se conservan en
`audit/validation-2026-10-29-crop-canvas-palette/` (carpeta local excluida de Git).
Los resultados aprobados son `validated-windows.xml` y `validated-ubuntu.xml`;
los logs de corridas anteriores se mantienen sólo para diagnóstico.

## Reproducir

```powershell
python scripts/verify.py -q --ignore=tests/ui --junitxml=reports/core.xml
python scripts/verify.py -q tests/ui --junitxml=reports/ui.xml
python scripts/ci/partitions.py
python -m ruff check app tests scripts
python -m pyright --pythonpath .venv/Scripts/python.exe
python -m scripts.ci.preflight --platform windows
git diff --check
```

En Ubuntu usar el intérprete del entorno completo, `xvfb-run -a` para las pruebas
y particiones, y `--platform linux` para preflight. En esta máquina el módulo
Tk 8.6 local se selecciona mediante `PYTHONPATH`; los runners de Actions usan su
Tk instalado. No se cambiaron las dependencias del proyecto.

Queda pendiente ejecutar los workflows modificados en Actions sobre
`windows-latest` y Ubuntu 22.04 después de autorizar commit/push. Esta ronda local
no valida un instalador ni un AppImage nuevos.
