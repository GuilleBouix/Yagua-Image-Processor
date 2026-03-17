"""
Ventana principal de la interfaz de usuario.
Contiene la estructura base con barra lateral y área de contenido.
"""

import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.module_registry import get_module_spec, iter_enabled_modules, load_frame_class

class MainWindow(ctk.CTkFrame):
    """Marco principal que contiene la barra lateral y el área de contenido."""
    
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)
        self.frames = {}
        self._build()
 
    def _build(self):
        """Construye los componentes de la ventana principal."""
        self.sidebar = Sidebar(self, on_select=self.show_module)
        self.sidebar.pack(side='left', fill='y')
        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.pack(side='left', fill='both', expand=True)
        
        for spec in iter_enabled_modules():
            self.frames[spec.key] = None

        self.show_module('compress')
    
    def show_module(self, key):
        """Muestra el módulo seleccionado."""
        if key not in self.frames:
            return
        if self.frames[key] is None:
            spec = get_module_spec(key)
            if not spec:
                return
            cls = load_frame_class(spec)
            frame = cls(self.content)
            frame.place(relwidth=1, relheight=1)
            self.frames[key] = frame
        self.frames[key].tkraise()
        self.sidebar.set_active(key)
