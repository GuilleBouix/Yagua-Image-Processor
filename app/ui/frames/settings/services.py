"""Servicios UI-agnosticos para gestionar y aplicar los ajustes."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping

from app.translations import AVAILABLE_LANGUAGES
from app.ui import colors
from app.ui.module_registry import iter_all_modules
from app.ui.scale import DEFAULT_UI_SCALE, VALID_UI_SCALES
from app.utils.settings import settings_path, load_settings, save_settings


def _settings_path() -> Path:
    """Obtener la ruta del archivo de configuracion de usuario."""
    return settings_path()


def _load_settings() -> dict:
    """Carga preferencias y devuelve valores predeterminados ante datos inválidos."""
    return load_settings(_settings_path())


def _save_settings(settings: dict) -> None:
    """Guarda las preferencias locales mediante el servicio compartido."""
    save_settings(settings, _settings_path())


def get_visible_modules() -> list[str] | None:
    """Retornar la lista de modulos visibles guardada."""
    settings = _load_settings()
    visible = settings.get('visible_modules')
    if not isinstance(visible, list):
        return None
    return [str(value) for value in visible]


def get_ui_scale() -> int:
    """Retornar la escala de UI guardada o el valor por defecto."""
    settings = _load_settings()
    value = settings.get('ui_scale', DEFAULT_UI_SCALE)
    try:
        scale = int(value)
    except (TypeError, ValueError):
        return DEFAULT_UI_SCALE
    return scale if scale in VALID_UI_SCALES else DEFAULT_UI_SCALE


def apply_settings_and_restart(
    *,
    language: str,
    theme: str,
    ui_scale: int,
    visible_modules: list[str],
) -> None:
    """Validar y guardar todos los ajustes antes de reiniciar una sola vez."""
    if language not in AVAILABLE_LANGUAGES:
        raise ValueError(f'Idioma no valido: {language}')
    if theme not in colors.get_theme_names():
        raise ValueError(f'Tema no valido: {theme}')
    if ui_scale not in VALID_UI_SCALES:
        raise ValueError(f'Escala de UI no valida: {ui_scale}')

    selected = set(visible_modules)
    selected.add('settings')
    modules = [spec.key for spec in iter_all_modules() if spec.key in selected]

    settings = _load_settings()
    settings.update({
        'language': language,
        'theme': theme,
        'ui_scale': ui_scale,
        'visible_modules': modules,
    })
    _save_settings(settings)
    restart_app()


def _restart_command(environ: Mapping[str, str] | None = None) -> list[str]:
    """Resolver el ejecutable estable que debe abrir la nueva instancia."""
    environment = os.environ if environ is None else environ
    arguments = sys.argv[1:]
    if getattr(sys, 'frozen', False):
        appimage = environment.get('APPIMAGE')
        if appimage and Path(appimage).is_file():
            return [appimage, *arguments]
        return [sys.executable, *arguments]
    return [sys.executable, str(Path(sys.argv[0]).resolve()), *arguments]


def _restart_environment(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Quitar referencias al montaje viejo sin perder el entorno grafico."""
    environment = dict(os.environ if environ is None else environ)
    if 'APPIMAGE' not in environment and 'APPDIR' not in environment:
        return environment

    for key in ('APPDIR', 'APPIMAGE', 'ARGV0'):
        environment.pop(key, None)

    original_library_path = environment.pop('LD_LIBRARY_PATH_ORIG', None)
    if original_library_path is None:
        environment.pop('LD_LIBRARY_PATH', None)
    else:
        environment['LD_LIBRARY_PATH'] = original_library_path
    return environment


def restart_app() -> None:
    """Abrir una nueva instancia y cerrar la actual."""
    from app.ui.operations import operations
    if operations.is_busy():
        import tkinter
        from tkinter import messagebox
        from app.translations import t
        root = getattr(tkinter, '_default_root', None)
        if root is None:
            raise RuntimeError('Cannot restart during an active operation')
        if messagebox.askyesno(t('app_title'), t('restart_when_idle'), parent=root):
            def wait():
                """Espera a que un reinicio o cierre diferido pueda continuar."""
                if operations.is_busy():
                    root.after(100, wait)
                else:
                    restart_app()
            root.after(100, wait)
        return
    command = _restart_command()
    environment = _restart_environment()
    if os.name == 'nt':
        subprocess.Popen(command, env=environment)
    else:
        subprocess.Popen(command, env=environment, start_new_session=True)
    sys.exit(0)


__all__ = [
    'apply_settings_and_restart',
    'get_ui_scale',
    'get_visible_modules',
    'restart_app',
]
