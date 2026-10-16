"""Bundled UI fonts, registered privately for the life of this process."""

import ctypes
import ctypes.util
import logging
from pathlib import Path
import sys
import tkinter.font as tkfont

import customtkinter as ctk

from app.translations import get_language
from app.utils.paths import resource_path

logger = logging.getLogger(__name__)
RUTA_FUENTE_INTER = 'assets/fonts/Inter.ttf'
CJK_FONTS = tuple(
    f'assets/fonts/noto-cjk/NotoSansCJK{region}-{weight}.otf'
    for region in ('jp', 'sc') for weight in ('Regular', 'Bold')
)
LANGUAGE_FAMILIES = {'日本語': 'Noto Sans CJK JP', '简体中文': 'Noto Sans CJK SC'}
_registered: set[Path] = set()
FUENTE_BASE = None
FUENTE_TITULO = None
FUENTE_CHICA = None


def _register_font(path: Path) -> bool:
    if sys.platform == 'win32':
        # FR_PRIVATE: available to this process only, removed by Windows on exit.
        library = ctypes.WinDLL('gdi32', use_last_error=True)
        add = library.AddFontResourceExW
        add.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
        add.restype = ctypes.c_int
        return add(str(path), 0x10, None) > 0
    if sys.platform.startswith('linux'):
        library = ctypes.CDLL(ctypes.util.find_library('fontconfig') or 'libfontconfig.so.1')
        current = library.FcConfigGetCurrent
        current.argtypes = []
        current.restype = ctypes.c_void_p
        add = library.FcConfigAppFontAddFile
        add.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        add.restype = ctypes.c_int
        config = current()
        return bool(config and add(config, bytes(path)))
    return False  # macOS remains experimental; use its normal system fallback.


def registrar_fuentes() -> dict[str, bool]:
    """No downloads or font installation; failures do not prevent startup."""
    results = {}
    for relative in (RUTA_FUENTE_INTER, *CJK_FONTS):
        path = resource_path(relative).resolve()
        try:
            loaded = path in _registered or (path.is_file() and _register_font(path))
            if loaded:
                _registered.add(path)
            else:
                logger.warning('Could not register bundled font: %s', path)
        except (OSError, AttributeError):
            logger.exception('Could not register bundled font: %s', path)
            loaded = False
        results[relative] = loaded
    return results


def cargar_fuente(ruta_fuente):
    """Compatibility helper for existing callers."""
    return tkfont.Font(family=Path(ruta_fuente).stem)


def fuente_selector_idiomas():
    # Native names must be readable before choosing/applying a CJK language.
    family = LANGUAGE_FAMILIES.get(get_language(), 'Noto Sans CJK JP')
    return ctk.CTkFont(family=family, size=14)


def inicializar_fuentes(language: str | None = None):
    global FUENTE_BASE, FUENTE_TITULO, FUENTE_CHICA
    registrar_fuentes()
    family = LANGUAGE_FAMILIES.get(language or get_language(), 'Inter')
    # Defaults also cover menus, dropdowns and controls without an explicit font.
    ctk.ThemeManager.theme['CTkFont']['family'] = family
    FUENTE_BASE = ctk.CTkFont(family=family, size=14)
    FUENTE_TITULO = ctk.CTkFont(family=family, size=22, weight='bold')
    FUENTE_CHICA = ctk.CTkFont(family=family, size=12)
