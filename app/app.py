"""
Aplicacion principal Yagua.
Contiene la clase principal que inicializa la ventana y componentes.

Relacionado con:
    - app/main.py: Punto de entrada que instancia esta clase.
    - app/ui/main_window.py: Contiene la ventana principal con sidebar y frames.
    - app/ui/fonts.py: Carga las fuentes personalizadas.
    - app/translations/__init__.py: Provee traducciones para el titulo.
"""

import logging
import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from app.ui import fonts
from app.utils.paths import resource_path
from app.ui.main_window import MainWindow
from app.translations import t

logger = logging.getLogger(__name__)


class YaguaApp(ctk.CTk):
    """
    Ventana principal de la aplicacion Yagua.
    
    Hereda de CTk (CustomTkinter) y es responsable de:
        - Configurar la ventana y su geometria.
        - Cargar fuentes personalizadas.
        - Establecer el icono de la aplicacion.
        - Crear e integrar MainWindow con sidebar y frames.
    """
    
    def __init__(self):
        """
        Inicializa la ventana principal.
        
        Configura titulo, geometria, fuentes, icono y el
        contenedor principal de la interfaz.
        """
        super().__init__()
        
        # Cargar fuentes personalizadas de la aplicacion
        fonts.inicializar_fuentes()
        
        # Establecer titulo de la ventana (traducible)
        self.title(t('app_title'))
        
        # Geometria inicial de la ventana
        self.geometry('1000x500')
        
        # Actualizar para asegurar que la geometria se aplique antes de maximizar
        self.update()
        
        # Maximizar ventana al iniciar
        if sys.platform == 'darwin':
            self.update_idletasks()
            w = self.winfo_screenwidth()
            h = self.winfo_screenheight()
            self.geometry(f'{w}x{h}+0+0')
        elif sys.platform == 'win32':
            try:
                self.state('zoomed')
            except Exception:
                self.update_idletasks()
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f'{w}x{h}+0+0')
        else:
            try:
                self.attributes('-zoomed', True)
            except Exception:
                self.update_idletasks()
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f'{w}x{h}+0+0')
        
        # Establecer tamano minimo de la ventana
        self.minsize(900, 600)
        
        # En macOS, restaurar la ventana al hacer click en el icono del Dock
        if sys.platform == 'darwin':
            self._setup_dock_reopen()
        
        # Configurar icono de la ventana segun plataforma
        self._setup_icon()
        
        # Crear ventana principal con sidebar y area de contenido
        self.main_window = MainWindow(self)
        self.main_window.pack(fill='both', expand=True)
    
    def _setup_dock_reopen(self):
        """Registra el handler para restaurar la ventana desde el Dock en macOS."""
        try:
            self.createcommand('tk::mac::ReopenApplication', self._on_dock_click)
        except Exception as e:
            logger.debug("No se pudo registrar ReopenApplication: %s", e)

    def _on_dock_click(self):
        """Restaura la ventana cuando el usuario hace click en el icono del Dock."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _setup_icon(self):
        """
        Configura el icono de la ventana segun la plataforma.
        
        Windows: icon.ico | macOS: icon.png (icon.icns para bundle) | Linux: icon.png
        """
        icon_ico = resource_path('assets/icon.ico')
        icon_icns = resource_path('assets/icon.icns')
        icon_png = resource_path('assets/icon.png')
        
        if sys.platform == 'win32':
            if icon_ico.exists():
                self.iconbitmap(str(icon_ico))
            elif icon_png.exists():
                self._setup_icon_png(icon_png)
            else:
                logger.warning("Icono no encontrado en assets/")
        elif sys.platform == 'darwin':
            if icon_png.exists():
                self._setup_icon_png(icon_png)
            elif icon_icns.exists():
                try:
                    self.iconbitmap(str(icon_icns))
                except Exception as e:
                    logger.warning(f'No se pudo aplicar icon.icns: {e}')
            else:
                logger.warning("Icono no encontrado en assets/")
        else:
            if icon_png.exists():
                self._setup_icon_png(icon_png)
            else:
                logger.warning("Icono no encontrado en assets/")
    
    def _setup_icon_png(self, icon_path):
        """
        Configura el icono desde archivo PNG.
        
        Args:
            icon_path: Ruta al archivo PNG del icono.
        """
        try:
            # Abrir imagen y convertir a RGBA para compatibilidad
            img = Image.open(icon_path).convert('RGBA')
            
            # Crear imagen para Tkinter
            img_tk = ImageTk.PhotoImage(img)
            
            # Asignar icono a la ventana
            self.iconphoto(True, img_tk)
        except Exception as e:
            logger.warning(f"Error al cargar icono: {e}")
