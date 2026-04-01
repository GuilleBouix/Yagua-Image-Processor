"""
Estado UI para el modulo de transformaciones geometricas.

Relacionado con:
    - app/ui/frames/image_transform/frame.py: Usa este estado.
"""

import customtkinter as ctk


class ImageTransformState:
    """Estado del modulo de transformaciones geometricas."""

    def __init__(self):
        """Inicializa el estado con valores por defecto."""
        self.imagenes = []

        # Rotacion rapida — valor interno o None
        self.rotacion_rapida = ctk.StringVar(value='')

        # Rotacion libre
        self.angulo_libre = ctk.IntVar(value=0)

        # Volteos
        self.flip_horizontal = ctk.BooleanVar(value=False)
        self.flip_vertical   = ctk.BooleanVar(value=False)

        # Correccion EXIF
        self.corregir_exif = ctk.BooleanVar(value=True)

    def obtener_opciones(self):
        """
        Construye el diccionario de opciones para el modulo.

        Returns:
            Diccionario con todas las transformaciones configuradas.
        """
        return {
            'rotacion_rapida':  self.rotacion_rapida.get() or None,
            'angulo_libre':     self.angulo_libre.get(),
            'flip_horizontal':  self.flip_horizontal.get(),
            'flip_vertical':    self.flip_vertical.get(),
            'corregir_exif':    self.corregir_exif.get(),
        }

    def resetear_rotacion_rapida(self):
        """Limpia la rotacion rapida seleccionada."""
        self.rotacion_rapida.set('')

    def resetear_angulo(self):
        """Resetea el angulo libre a 0."""
        self.angulo_libre.set(0)

    def hay_transformaciones(self):
        """
        Verifica si hay al menos una transformacion activa.

        Returns:
            True si hay algo que aplicar, False si no.
        """
        return (
            bool(self.rotacion_rapida.get()) or
            self.angulo_libre.get() != 0 or
            self.flip_horizontal.get() or
            self.flip_vertical.get() or
            self.corregir_exif.get()
        )