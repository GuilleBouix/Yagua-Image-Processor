"""
Ventana principal de la interfaz de usuario.
Contiene la estructura base con barra lateral y area de contenido.

Relacionado con:
    - app/app.py: Crea e integra esta ventana.
    - app/ui/sidebar.py: Barra lateral de navegacion.
    - app/ui/module_registry.py: Registro de modulos disponibles.
    - app/ui/frames/: Frames de cada modulo.
"""

import customtkinter as ctk

from app.ui.sidebar import Sidebar
from app.ui.module_registry import get_module_spec, iter_enabled_modules, load_frame_class


class MainWindow(ctk.CTkFrame):
    """
    Marco principal que contiene la barra lateral y el area de contenido.
    
    Organiza la interfaz en dos areas principales:
        - Sidebar: Barra lateral con botones de navegacion.
        - Content: Area donde se muestran los frames de cada modulo.
    """
    
    def __init__(self, parent):
        """
        Inicializa la ventana principal.
        
        Args:
            parent: Widget padre (normalmente la instancia de YaguaApp).
        """
        super().__init__(parent, corner_radius=0)
        
        # Diccionario para almacenar las instancias de frames (lazy-loaded)
        self.frames = {}
        
        # Construir la estructura de la ventana
        self._build()
  
    def _build(self):
        """
        Construye los componentes de la ventana principal.
        
        Crea la sidebar con sus botones y el area de contenido
        donde se mostraran los frames de cada modulo.
        """
        # Crear sidebar y posicionar a la izquierda
        self.sidebar = Sidebar(self, on_select=self.show_module)
        self.sidebar.pack(side='left', fill='y')
        
        # Crear area de contenido y posicionar a la derecha
        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.pack(side='left', fill='both', expand=True)
        
        # Inicializar slots para frames lazy-loaded
        first_key = None
        for spec in iter_enabled_modules():
            self.frames[spec.key] = None
            if first_key is None:
                first_key = spec.key

        # Mostrar el primer modulo visible por defecto
        if first_key is None:
            first_key = 'settings'
        self.show_module(first_key)
    
    def show_module(self, key):
        """
        Muestra el modulo seleccionado en el area de contenido.
        
        Si el frame del modulo no existe aun, lo crea bajo demanda
        (lazy loading) para mejorar el rendimiento de inicio.
        
        Args:
            key: Identificador del modulo a mostrar.
        """
        # Verificar que la key exista en los frames
        if key not in self.frames:
            return
        
        # Crear frame si no existe (lazy loading)
        if self.frames[key] is None:
            spec = get_module_spec(key)
            if not spec:
                return
            
            # Cargar la clase del frame dinamicamente
            cls = load_frame_class(spec)
            
            # Crear instancia del frame en el area de contenido
            frame = cls(self.content)
            frame.place(relwidth=1, relheight=1)
            self.frames[key] = frame
        
        # Traer el frame al frente
        self.frames[key].tkraise()
        
        # Actualizar boton activo en la sidebar
        self.sidebar.set_active(key)
