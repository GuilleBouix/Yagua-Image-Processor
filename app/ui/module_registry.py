"""
Registry central de mÃ³dulos para sidebar y navegaciÃ³n.
Evita desincronizaciones y permite lazy-load de frames.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Iterable

import customtkinter as ctk


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label_key: str
    icon_path: str
    frame_import: str
    enabled: bool = True


_MODULE_SPECS: list[ModuleSpec] = [
    ModuleSpec('compress', 'compress', 'assets/icons/compress.png', 'app.ui.frames.compress.frame:CompressFrame'),
    ModuleSpec('convert', 'convert', 'assets/icons/convert.png', 'app.ui.frames.convert.frame:ConvertFrame'),
    ModuleSpec('remove_bg', 'remove_bg', 'assets/icons/remove_background.png', 'app.ui.frames.remove_bg_frame:RemoveBgFrame'),
    ModuleSpec('resize', 'resize', 'assets/icons/resize.png', 'app.ui.frames.resize.frame:ResizeFrame'),
    ModuleSpec('rename', 'rename', 'assets/icons/rename.png', 'app.ui.frames.rename_frame:RenameFrame'),
    ModuleSpec('palette', 'palette', 'assets/icons/palette.png', 'app.ui.frames.palette.frame:PaletteFrame'),
    ModuleSpec('watermark', 'watermark', 'assets/icons/watermark.png', 'app.ui.frames.watermark_frame:WatermarkFrame'),
    ModuleSpec('metadata', 'metadata', 'assets/icons/metadata.png', 'app.ui.frames.metadata.frame:MetadataFrame'),
    ModuleSpec('lqip', 'lqip', 'assets/icons/lqip.png', 'app.ui.frames.lqip_frame:LQIPFrame'),
    ModuleSpec('optimizer', 'optimizer', 'assets/icons/optimizer.png', 'app.ui.frames.optimizer_frame:OptimizerFrame'),
    ModuleSpec('settings', 'settings', 'assets/icons/settings.png', 'app.ui.frames.settings.frame:SettingsFrame'),
]


def iter_enabled_modules() -> Iterable[ModuleSpec]:
    return (m for m in _MODULE_SPECS if m.enabled)


def get_module_spec(key: str) -> ModuleSpec | None:
    for m in _MODULE_SPECS:
        if m.key == key:
            return m
    return None


def load_frame_class(spec: ModuleSpec) -> type[ctk.CTkFrame]:
    """Importa el frame bajo demanda."""
    module_name, class_name = spec.frame_import.split(':', 1)
    mod = importlib.import_module(module_name)
    return getattr(mod, class_name)
