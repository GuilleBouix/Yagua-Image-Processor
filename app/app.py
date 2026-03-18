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
        
        # Maximizar ventana al iniciar (solo funciona en Windows)
        self.state('zoomed')
        
        # Establecer tamano minimo de la ventana
        self.minsize(900, 600)
        
        # Configurar icono de la ventana segun plataforma
        self._setup_icon()
        
        # Crear ventana principal con sidebar y area de contenido
        self.main_window = MainWindow(self)
        self.main_window.pack(fill='both', expand=True)
    
    def _setup_icon(self):
        """
        Configura el icono de la ventana segun la plataforma.
        
        En Windows usa icon.ico, en otras plataformas usa icon.png.
        Registra warnings si los iconos no se encuentran.
        """
        # Rutas de los archivos de icono
        icon_ico = Path('assets/icon.ico')
        icon_png = Path('assets/icon.png')
        
        # Configuracion especifica para Windows
        if sys.platform == 'win32':
            # Usar .ico en Windows (formato nativo)
            if icon_ico.exists():
                self.iconbitmap(str(icon_ico))
            # Fallback a PNG si .ico no existe
            elif icon_png.exists():
                self._setup_icon_png(icon_png)
            else:
                # Registrar warning si no hay icono disponible
                logger.warning("Icono no encontrado en assets/")
        else:
            # En otras plataformas solo usar PNG
            if icon_png.exists():
                self._setup_icon_png(icon_png)
            elif icon_ico.exists():
                # .ico no es compatible con macOS/Linux
                logger.warning("icon.ico no es compatible con esta plataforma")
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
