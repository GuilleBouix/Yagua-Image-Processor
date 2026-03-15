"""
Ventana principal de la interfaz de usuario.
Contiene la estructura base con barra lateral y área de contenido.
"""

import customtkinter as ctk
from ui.sidebar import Sidebar
from ui.frames.compress_frame import CompressFrame
from ui.frames.convert_frame import ConvertFrame
from ui.frames.remove_bg_frame import RemoveBgFrame
from ui.frames.resize_frame import ResizeFrame
from ui.frames.rename_frame import RenameFrame
from ui.frames.palette_frame import PaletteFrame
from ui.frames.watermark_frame import WatermarkFrame
from ui.frames.metadata_frame import MetadataFrame
from ui.frames.lqip_frame import LQIPFrame
from ui.frames.optimizer_frame import OptimizerFrame

MODULOS = {
    'compress': ('Comprimir', CompressFrame),
    'convert': ('Convertir', ConvertFrame),
    'remove_bg': ('Quitar fondo', RemoveBgFrame),
    'resize': ('Redimensionar', ResizeFrame),
    'rename': ('Renombrar lote', RenameFrame),
    'palette': ('Paleta colores', PaletteFrame),
    'watermark': ('Watermark', WatermarkFrame),
    'metadata': ('Metadatos EXIF', MetadataFrame),
    'lqip': ('LQIP / Base64', LQIPFrame),
    'optimizer': ('Smart Optimizer', OptimizerFrame),
}

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
        
        for key, (label, cls) in MODULOS.items():
            frame = cls(self.content)
            frame.place(relwidth=1, relheight=1)
            self.frames[key] = frame
        
        self.show_module('compress')
    
    def show_module(self, key):
        """Muestra el módulo seleccionado."""
        self.frames[key].tkraise()
        self.sidebar.set_active(key)