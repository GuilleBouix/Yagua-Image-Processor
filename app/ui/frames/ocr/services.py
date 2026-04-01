"""
Servicios para el modulo de OCR.
Re-exporta las funciones del modulo de logica pura.

Relacionado con:
    - app/ui/frames/ocr/frame.py: Usa estos servicios.
    - app/modules/ocr.py: Modulo de logica pura.
"""

from app.modules.ocr import batch_procesar, exportar_texto, ensure_reader

__all__ = ['batch_procesar', 'exportar_texto', 'ensure_reader']
