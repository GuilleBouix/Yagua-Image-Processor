"""
Registry central de modulos para sidebar y navegacion.
Evita desincronizaciones y permite lazy-load de frames.

Relacionado con:
    - app/ui/sidebar.py: Usa este registry para construir los botones.
    - app/ui/main_window.py: Usa este registry para cargar frames.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import logging
from typing import List, Optional

from app.utils.settings import settings_path, load_settings


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ModuleSpec:
    """
    Especificacion de un modulo de la aplicacion.
    
    Define la informacion necesaria para crear el boton
    en la sidebar y cargar el frame correspondiente.
    
    Attributes:
        key: Identificador unico del modulo.
        label_key: Clave de traduccion para el label.
        icon_path: Ruta al archivo de icono.
        frame_import: Ruta de importacion del frame (modulo:Clase).
        enabled: Si el modulo esta habilitado.
    """
    key: str
    label_key: str
    icon_path: str
    frame_import: str
    enabled: bool = True
    preload_ui: bool = False


# Registro de todos los modulos disponibles
_MODULE_SPECS = [
    ModuleSpec(
        'convert',
        'convert',
        'assets/icons/convert.png',
        'app.ui.frames.convert.frame:ConvertFrame',
        preload_ui=True,
    ),
    ModuleSpec(
        'compress',
        'compress',
        'assets/icons/compress.png',
        'app.ui.frames.compress.frame:CompressFrame',
        preload_ui=True,
    ),
    ModuleSpec(
        'resize',
        'resize',
        'assets/icons/resize.png',
        'app.ui.frames.resize.frame:ResizeFrame',
        preload_ui=True,
    ),
    ModuleSpec(
        'remove_bg',
        'remove_bg',
        'assets/icons/remove_background.png',
        'app.ui.frames.remove_bg.frame:RemoveBgFrame',
    ),
    ModuleSpec(
        'palette',
        'palette',
        'assets/icons/palette.png',
        'app.ui.frames.palette.frame:PaletteFrame',
        preload_ui=True,
    ),
    ModuleSpec(
        "watermark",
        "watermark",
        "assets/icons/watermark.png",
        "app.ui.frames.watermark.frame:WatermarkFrame",
        preload_ui=True,
    ),
    ModuleSpec(
        'rename',
        'rename',
        'assets/icons/rename.png',
        'app.ui.frames.rename.frame:RenameFrame',
        preload_ui=True,
    ),
    ModuleSpec(
        'ocr',
        'ocr',
        'assets/icons/ocr.png',
        'app.ui.frames.ocr.frame:OcrFrame',
    ),
    ModuleSpec(
        'metadata',
        'metadata',
        'assets/icons/metadata.png',
        'app.ui.frames.metadata.frame:MetadataFrame',
        preload_ui=True,
    ),
    ModuleSpec(
        'lqip',
        'lqip',
        'assets/icons/lqip.png',
        'app.ui.frames.lqip.frame:LqipFrame',
        preload_ui=True,
    ),
    ModuleSpec(
        'settings',
        'settings',
        'assets/icons/settings.png',
        'app.ui.frames.settings.frame:SettingsFrame',
        preload_ui=True,
    )
]


def iter_enabled_modules():
    """
    Itera sobre los modulos habilitados.
    
    Yields:
        ModuleSpec para cada modulo con enabled=True.
    """
    visible = _get_visible_modules()
    if not visible:
        return (m for m in _MODULE_SPECS if m.enabled)
    visible_set = set(visible)
    visible_set.add('settings')
    return (m for m in _MODULE_SPECS if m.enabled and m.key in visible_set)


def iter_all_modules() -> List[ModuleSpec]:
    """Retorna la lista completa de modulos registrados."""
    return list(_MODULE_SPECS)


def _get_visible_modules() -> Optional[List[str]]:
    """Lee visible_modules desde user_settings.json si existe."""
    data = load_settings(settings_path())
    visible = data.get('visible_modules')
    if not isinstance(visible, list):
        return None
    return [str(v) for v in visible]


def get_module_spec(key):
    """
    Obtiene la especificacion de un modulo por su key.
    
    Args:
        key: Identificador del modulo.
        
    Returns:
        ModuleSpec del modulo o None si no existe.
    """
    for m in _MODULE_SPECS:
        if m.key == key:
            return m
    return None


def load_frame_class(spec):
    """
    Importa la clase del frame bajo demanda.
    
    Usa importlib para cargar el modulo y obtener la clase
    sin necesidad de importarlo al inicio de la aplicacion.
    
    Args:
        spec: ModuleSpec con la informacion de importacion.
        
    Returns:
        Clase del frame lista para instanciar.
    """
    # Separar nombre del modulo y nombre de la clase
    module_name, class_name = spec.frame_import.split(':', 1)
    
    try:
        logger.info(
            "module_registry: cargar_frame (key=%s, module=%s, class=%s)",
            spec.key, module_name, class_name
        )
        # Importar el modulo dinámicamente
        mod = importlib.import_module(module_name)
        # Obtener y retornar la clase
        return getattr(mod, class_name)
    except Exception:
        logger.exception(
            "module_registry: error cargando frame (key=%s, module=%s, class=%s)",
            spec.key, module_name, class_name
        )
        raise
