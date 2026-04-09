# Ajustes

## Overview
Permite configurar idioma, tema, módulos visibles y consultar actualizaciones.

## Inputs soportados
- Configuración de usuario (se guarda en `user_settings.json`).

## Outputs
- Cambios persistidos para próximos inicios.

## Workflow
### Ajustes
- Cambiar idioma/tema y módulos visibles.

### Actualizaciones
- “Buscar actualizaciones” verifica si hay una versión más nueva.
- Si existe, muestra un botón/enlace para abrir la Release en GitHub y descargar manualmente.

## Errores comunes
- Sin internet: el check de updates puede fallar (se muestra estado de error).

## Troubleshooting
- Logs:
  - Windows: `%APPDATA%\\Yagua\\yagua.log`
  - Linux: `~/.config/Yagua/yagua.log`
  - macOS: `~/Library/Application Support/Yagua/yagua.log`

## Ejemplos
- Cambiar idioma a English y ocultar módulos no usados.

## Notas técnicas
- El check de updates usa `latest.json` del release “latest” del repo.

## Limitaciones
- No instala actualizaciones automáticamente (descarga e instalación son manuales).

## Performance tips
- Si la ventana tarda al abrir: revisar tamaño de logs y rendimiento del disco.

