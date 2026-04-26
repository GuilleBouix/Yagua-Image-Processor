"""
Estado UI para el modulo de eliminacion de fondo.

Relacionado con:
    - app/ui/frames/remove_bg/frame.py: Usa este estado.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RemoveBgState:
    """
    Estado liviano del modulo de eliminacion de fondo.

    Attributes:
        model_used: Nombre del modelo utilizado en el ultimo proceso.
        used_fallback: Indica si se uso el modelo de compatibilidad.
    """

    model_used: str | None = None
    used_fallback: bool = False

    def set_model_info(self, model_used: str | None, used_fallback: bool) -> None:
        """Actualiza la metadata del ultimo procesamiento."""
        self.model_used = model_used
        self.used_fallback = used_fallback
