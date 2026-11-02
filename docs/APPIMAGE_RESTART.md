# Reinicio del AppImage al aplicar Ajustes

Idioma, tema, escala y módulos visibles se guardan juntos antes de abrir una
instancia nueva. El comando debe usar el archivo AppImage original, nunca el
ejecutable de su montaje temporal.

AppRun modifica rutas de bibliotecas, cargadores, hooks, `PATH` y directorios
XDG. `_restart_environment` restaura sus valores `APPRUN_ORIGINAL_*` y elimina
el estado privado `APPRUN_*`/`APPDIR_*` del montaje anterior. El
`LD_LIBRARY_PATH_ORIG` de PyInstaller por sí solo no es suficiente: puede
contener rutas que AppRun ya había modificado. Se conserva el entorno gráfico
y las opciones del usuario, como `APPIMAGE_EXTRACT_AND_RUN`, y se solicita a
PyInstaller una instancia independiente con `PYINSTALLER_RESET_ENVIRONMENT`.

## Verificación del paquete real

La etapa Linux `probe` ejecuta `scripts/ci/probe_restart.py` sobre el AppImage,
además de las comprobaciones de arranque, formatos y modelos existentes.

```sh
xvfb-run -a python scripts/ci/probe_restart.py /ruta/Yagua.AppImage /ruta/nueva/informe
```

También puede ejecutarse sin Xvfb desde un escritorio X11. El directorio del
informe debe ser nuevo. La prueba usa un perfil aislado y eventos reales de Tk:
abre Ajustes, cambia idioma/tema/escala y pulsa Aplicar tres veces. Exige que
desaparezca la instancia anterior, que haya un PID nuevo, que termine el splash
y que Inicio y Ajustes se muestren en el idioma y la escala elegidos. Comprueba
también que las preferencias y los valores visibles coincidan. No sustituye
la función de reinicio ni sus callbacks.

Para evitar falsos fallos en versiones de Tk de escritorio, espera la salida
del PID anterior y renueva la conexión de control X11 antes de buscar la nueva
ventana. Identifica las ventanas por el perfil de prueba y su PID, porque los
nombres de intérprete pueden reutilizarse. La lectura momentánea de `/proc`
durante un `exec` no se usa para declarar fallida una apertura: se exige la
interfaz lista dentro del tiempo límite.

Si el reemplazo se cierra, conserva `restart.json` y `process.log` y falla la
etapa. Esos diagnósticos se suben incluso cuando falla el job. Un cambio de la
prueba invalida el checkpoint `probe`, conservando las compilaciones compatibles.

No alcanza con comprobar que la ruta del AppImage exista o que `Popen` haya
devuelto un proceso: eso no demuestra que la interfaz se haya vuelto a abrir.
