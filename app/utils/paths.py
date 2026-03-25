"""
Helper para resolver rutas de recursos en modo dev y en .exe (PyInstaller).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


logger = logging.getLogger(__name__)


def resource_path(rel_path: str) -> Path:
    """
    Resuelve una ruta relativa a recursos tanto en desarrollo
    como en un ejecutable generado con PyInstaller.

    Args:
        rel_path: Ruta relativa dentro del proyecto (ej: 'assets/icon.png').

    Returns:
        Path absoluto al recurso.
    """
    base_dir = getattr(sys, '_MEIPASS', None)
    if base_dir:
        path = Path(base_dir) / rel_path
    else:
        # Repo root: app/utils/paths.py -> app/utils -> app -> repo root
        path = Path(__file__).resolve().parents[2] / rel_path

    if not path.exists():
        logger.warning("Recurso no encontrado: %s", path)
    return path


__all__ = ['resource_path']
